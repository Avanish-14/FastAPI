from fastapi import FastAPI , Path ,HTTPException ,Query ,Depends,status
from pydantic import BaseModel , Field, computed_field
from typing import Annotated ,Literal , Optional
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import json

class Patient(BaseModel):
    id:Annotated[str,Field(...,description='Id of the patient',example="P001")]
    name:Annotated[str,Field(...,max_length=50,description='Name of the patient',example="John Doe")]
    city:Annotated[str,Field(...,description="name of the city")]
    age:Annotated[int,Field(...,gt=0,lt=100,description='Age of the patient',example=30)]
    gender:Annotated[Literal['male','female','others'],Field(...,description="Gender of the patinet")]
    height:Annotated[float,Field(...,gt=0,description="hienght of the patient in metres")]
    weight:Annotated[float,Field(...,gt=0,description="Wieght of the patient in kg")]
    
    @computed_field(return_type=float)
    @property
    def bmi(self) -> float: # float is the return type
        return round(self.weight/(self.height**2),2)
    
    @computed_field(return_type= str)
    @property
    def verdict(self) -> str:
        if self.bmi<18.5:
            return "Underweight"
        elif self.bmi<25:
            return "Normal"
        elif self.bmi <30:
            return "Overweight"
        else :
            return "obese"
        
class PatientUpdate(BaseModel):
    name:Annotated[Optional[str],Field(default=None)]
    city:Annotated[Optional[str],Field(default=None)]
    age :Annotated[Optional[int],Field(default=None)]
    gender:Annotated[Optional[Literal['male','females']],Field(default=None)]
    height:Annotated[Optional[float],Field(default=None,gt=0)]
    weight:Annotated[Optional[float],Field(default=None,gt=0)]
    
            
    
    


app = FastAPI() # app ek fast API ka object hai

#Authentication
# depends methods is used to get the token from the header
oauth_scheme = OAuth2PasswordBearer(tokenUrl='token')

FAKE_USERNAME = "admin"
FAKE_PASSWORD = "admin123"
FAKE_TOKEN = "faketoken123" 

@app.post("/token")
async def token_generate(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == FAKE_USERNAME and form_data.password == FAKE_PASSWORD:
        return {"access_token": FAKE_TOKEN, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

def verify_token(token: str = Depends(oauth_scheme)):
    if token != FAKE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    
def load_data(): # ye function data patient.json se leke aata hai or data naam ke  variable me load karke return karta hai
    with open('patients.json','r') as f:
        data = json.load(f)
        return data
    
def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data,f)
        
@app.get("/")
def hello():
    return {"message": "Patient management system API"}

@app.get('/about')
def about():
    return {'message':'A fully function API to manage your patients record'}

@app.get('/view') # creating an endpoint to view the data
def view():
    data = load_data() # calling the load_data fuction and store that data in tha data named varible then return  that data
    return data

@app.get('/view/{patient_id}')
def view_patient(patient_id: str = Path(...,description='ID of the patient in the DB',example ='P001')): # creating an endpoint to view the data of a specific patient
    # Path ka use karte hai apne endpoint ka discreption dene ke liye 
    # Why str becoz patient_id is a string
    data = load_data() # calling the load_data fuction and store that data in tha data named varibl
    
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404 , detail = "Patient not found")
@app.get('/sort')
# sort_by me 3 dots dene ka mtlb ki ye required parameter hai n ki optional parameter hai
def sort_patients(sort_by:str= Query(...,description="Sort on the basis of height,wieght or bmi"),order :str=Query('asc',description='Sort in ascending or desencing order')):
    valid_fields = ['height','weight','bmi']
    
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,detail="Invalid filed selected")
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400,detail='Selct oder  between ascending and dsencing') 
    data = load_data()
    flag = False
    if order == 'desc':
        flag = True
    sorted_data = sorted(data.values(),key=lambda x:float(x.get(sort_by,0)),reverse= flag)
    return sorted_data
    
    #data.values() will returen the json without the keys(patients_id)
    
   # key=lambda x: x.get(sort_by, 0)
#This part tells Python how to sort the items.

#x is each patient dictionary (e.g., {"name": "John", "age": 30})

#x.get(sort_by, 0):

#Tries to get the value from that dict using the variable sort_by

#If sort_by = "age", it does x.get("age")

#If the key is missing, it returns 0 by default (avoids crash)


@app.post('/create') # new end point uses pydantic model
def create_patient(patient:Patient,token:str=Depends(verify_token)): # jiss type ka dat revice karenge vo Patient type ka hoga
    #load the existing data
    data = load_data()
    
    #check if  the  patient id already exists
    if patient.id in data:
        raise HTTPException(status_code=400,detail="Patient already exits")
    
    #new patient add to the  database
    data[patient.id] = patient.model_dump(exclude=['id']) # model.dump chnage pydantic model into a dictionary ,exclude id koi id ke alag key hai apne data base me
    
    # save into the json file
    save_data(data) # apne data ko save kar lena hai
    
    return JSONResponse(status_code=201,content={'message':'patinet created successfully'}) # 201 is the status code for created
    
@app.put('/edit/{patient_id}')
def update_patient(patient_id:str,patient_update: PatientUpdate):
    
    data = load_data()
    
    if patient_id not in data:
        raise HTTPException(status_code=404,detail = 'Patinet not Found')    
    
    existing_patient_info = data[patient_id] # jo id user enter ki hai uss id ki dictoinary ko utha ke existing_patient_info is stre kar do
    update_patient_info=patient_update.model_dump(exclude_unset= True) # pyddantic model ko dictionary me  dump kar rahe hai , exclude_unset=True bus pydantantic model me selected field ko hi dictionary me convert karega
    
    for key,value in update_patient_info.items():
        existing_patient_info[key] = value # existing_patient_info me jo value update_patient_info me hai
        #us value ko update karega
    #existing_patient_info -> pydantic object -> updated bmi +verdict
    existing_patient_info['id'] =patient_id
    patient_pydantic_obj = Patient(**existing_patient_info) # pydantic object banane ke liye
    # pydantic object -> dictt
    existing_patient_info= patient_pydantic_obj.model_dump(exclude=['id'])
    
    # add this ti the dictonary
    data[patient_id] =existing_patient_info
    save_data(data)
    return JSONResponse(status_code=200 ,content={'message':'Patient updated successfully'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data = load_data()
    
    if patient_id not in data:
        raise HTTPException(status_code=404,detail = 'Patinet not Found')
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200,content={'message':'Patient deleted succesfully'})
    