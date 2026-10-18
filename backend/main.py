
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, Integer, String
from backend.database import engine, Base, SessionLocal

app = FastAPI(title="LifeLine AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database model
class EmergencyRecord(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String, unique=True, index=True, nullable=True)
    resource = Column(String, nullable=False)
    blood_group = Column(String, default="N/A")
    units = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, default="Pending")
    urgency = Column(String, default="Normal", nullable=False)


Base.metadata.create_all(bind=engine)


# Validate incoming emergency requests
class EmergencyRequest(BaseModel):
    resource: str
    blood_group: str
    units: int = Field(gt=0)
    location: str = Field(min_length=2)
    urgency: str = "Normal"

    @field_validator("resource")
    @classmethod
    def validate_resource(cls, value):
        allowed = ["Blood", "Medical Supplies", "Ambulance"]

        if value not in allowed:
            raise ValueError("Invalid resource type")

        return value

    @field_validator("location")
    @classmethod
    def validate_location(cls, value):
        value = value.strip()

        if len(value) < 2 or value.lower() == "string":
            raise ValueError("Enter a valid location")

        return value

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, value):
        allowed = ["Critical", "High", "Normal", "Low"]

        if value not in allowed:
            raise ValueError("Invalid urgency level")

        return value


# Validate status updates
class StatusUpdate(BaseModel):
    status: str


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to LifeLine AI!",
        "status": "Running successfully"
    }


# Submit an emergency request
@app.post("/request")
def submit_request(request: EmergencyRequest):
    db = SessionLocal()

    try:
        new_request = EmergencyRecord(
            resource=request.resource,
            blood_group=request.blood_group,
            units=request.units,
            location=request.location,
            status="Pending",
            urgency=request.urgency
        )

        db.add(new_request)
        db.commit()
        db.refresh(new_request)

        # Generate a readable request code.
        new_request.request_code = f"LL-{new_request.id:04d}"
        db.commit()
        db.refresh(new_request)

        return {
            "message": "Emergency request received successfully!",
            "request": {
                "request_id": new_request.id,
                "request_code": new_request.request_code,
                "resource": new_request.resource,
                "blood_group": new_request.blood_group,
                "units": new_request.units,
                "location": new_request.location,
                "status": new_request.status,
                "urgency": new_request.urgency
            }
        }

    finally:
        db.close()


# Retrieve all emergency requests
@app.get("/requests")
def get_requests():
    db = SessionLocal()

    try:
        requests = db.query(EmergencyRecord).order_by(
            EmergencyRecord.id.desc()
        ).all()

        # Generate and save codes for older records if missing.
        for item in requests:
            if not item.request_code:
                item.request_code = f"LL-{item.id:04d}"

        db.commit()

        return {
            "total_requests": len(requests),
            "requests": [
                {
                    "request_id": item.id,
                    "request_code": item.request_code,
                    "resource": item.resource,
                    "blood_group": item.blood_group,
                    "units": item.units,
                    "location": item.location,
                    "status": item.status,
                    "urgency": item.urgency
                }
                for item in requests
            ]
        }

    finally:
        db.close()


# Update the status of an emergency request
@app.put("/requests/{request_id}/status")
def update_request_status(request_id: int, update: StatusUpdate):
    allowed_statuses = ["Pending", "In Progress", "Resolved"]

    if update.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    db = SessionLocal()

    try:
        record = db.query(EmergencyRecord).filter(
            EmergencyRecord.id == request_id
        ).first()

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Request not found"
            )

        record.status = update.status
        db.commit()

        return {
            "message": "Status updated successfully",
            "request_id": record.id,
            "request_code": record.request_code,
            "status": record.status
        }

    finally:
        db.close()


# Delete only known invalid test records
@app.delete("/requests/test-data")
def delete_test_data():
    db = SessionLocal()

    try:
        test_requests = db.query(EmergencyRecord).filter(
            EmergencyRecord.resource == "string",
            EmergencyRecord.blood_group == "string",
            EmergencyRecord.location == "string",
            EmergencyRecord.units == 0
        ).all()

        deleted_count = len(test_requests)

        for item in test_requests:
            db.delete(item)

        db.commit()

        return {
            "message": "Test data cleaned successfully",
            "deleted_count": deleted_count
        }

    finally:
        db.close()
