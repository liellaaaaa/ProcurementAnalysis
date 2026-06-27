from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.models.database import Feedback, Satisfaction
from backend.services.operation_logger import OperationLogger

router = APIRouter(prefix="/api/v1/feedback", tags=["采购反馈"])


# ============ Pydantic Models ============

class FeedbackCreate(BaseModel):
    feedback_date: datetime
    current_status: str
    expected_result: str
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    rating: Optional[int] = None


class FeedbackUpdate(BaseModel):
    feedback_date: Optional[str] = None
    current_status: Optional[str] = None
    expected_result: Optional[str] = None
    is_resolved: Optional[bool] = None
    resolved_at: Optional[str] = None
    rating: Optional[int] = None


class FeedbackResponse(BaseModel):
    id: int
    feedback_date: str
    current_status: str
    expected_result: str
    is_resolved: bool
    resolved_at: Optional[str] = None
    rating: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SatisfactionCreate(BaseModel):
    score: int
    complaint: str


class SatisfactionUpdate(BaseModel):
    score: Optional[int] = None
    complaint: Optional[str] = None


class SatisfactionResponse(BaseModel):
    id: int
    score: int
    complaint: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============ Feedback CRUD ============

@router.get("/feedbacks", response_model=List[FeedbackResponse])
async def get_feedbacks(is_resolved: Optional[bool] = None, db: Session = Depends(get_db)):
    """获取反馈列表"""
    query = db.query(Feedback)
    if is_resolved is not None:
        query = query.filter(Feedback.is_resolved == is_resolved)
    results = query.order_by(Feedback.feedback_date.desc()).all()
    return [_feedback_to_response(f) for f in results]


@router.post("/feedbacks", response_model=FeedbackResponse)
async def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """创建反馈"""
    feedback_date_str = feedback.feedback_date.strftime("%Y-%m-%d") if isinstance(feedback.feedback_date, datetime) else str(feedback.feedback_date).split("T")[0]
    resolved_at_str = feedback.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if feedback.resolved_at else None

    new_feedback = Feedback(
        feedback_date=feedback_date_str,
        current_status=feedback.current_status,
        expected_result=feedback.expected_result,
        is_resolved=feedback.is_resolved,
        resolved_at=resolved_at_str,
        rating=feedback.rating
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)

    OperationLogger.log(OperationLogger.MODULE_SYSTEM, OperationLogger.OP_CREATE, {
        "module": "FEEDBACK", "action": "create_feedback"
    })

    return _feedback_to_response(new_feedback)


@router.put("/feedbacks/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(feedback_id: int, feedback: FeedbackUpdate, db: Session = Depends(get_db)):
    """更新反馈"""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not db_feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    if feedback.feedback_date is not None:
        db_feedback.feedback_date = str(feedback.feedback_date).split("T")[0]
    if feedback.current_status is not None:
        db_feedback.current_status = feedback.current_status
    if feedback.expected_result is not None:
        db_feedback.expected_result = feedback.expected_result
    if feedback.is_resolved is not None:
        db_feedback.is_resolved = feedback.is_resolved
    if feedback.resolved_at is not None:
        db_feedback.resolved_at = str(feedback.resolved_at)
    if feedback.rating is not None:
        db_feedback.rating = feedback.rating

    db_feedback.updated_at = datetime.now()
    db.commit()
    db.refresh(db_feedback)

    return _feedback_to_response(db_feedback)


@router.delete("/feedbacks/{feedback_id}")
async def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """删除反馈"""
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not db_feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    db.delete(db_feedback)
    db.commit()
    return {"message": "反馈已删除"}


# ============ Satisfaction CRUD ============

@router.get("/satisfactions", response_model=List[SatisfactionResponse])
async def get_satisfactions(db: Session = Depends(get_db)):
    """获取满意度记录列表"""
    results = db.query(Satisfaction).order_by(Satisfaction.created_at.desc()).all()
    return [_sat_to_response(s) for s in results]


@router.post("/satisfactions", response_model=SatisfactionResponse)
async def create_satisfaction(record: SatisfactionCreate, db: Session = Depends(get_db)):
    """创建满意度记录"""
    if not (1 <= record.score <= 10):
        raise HTTPException(status_code=400, detail="评分必须在1-10之间")

    new_record = Satisfaction(score=record.score, complaint=record.complaint)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    OperationLogger.log(OperationLogger.MODULE_SYSTEM, OperationLogger.OP_CREATE, {
        "module": "FEEDBACK", "action": "create_satisfaction"
    })

    return _sat_to_response(new_record)


@router.put("/satisfactions/{record_id}", response_model=SatisfactionResponse)
async def update_satisfaction(record_id: int, record: SatisfactionUpdate, db: Session = Depends(get_db)):
    """更新满意度记录"""
    db_record = db.query(Satisfaction).filter(Satisfaction.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="记录不存在")

    if record.score is not None:
        if not (1 <= record.score <= 10):
            raise HTTPException(status_code=400, detail="评分必须在1-10之间")
        db_record.score = record.score
    if record.complaint is not None:
        db_record.complaint = record.complaint

    db_record.updated_at = datetime.now()
    db.commit()
    db.refresh(db_record)

    return _sat_to_response(db_record)


@router.delete("/satisfactions/{record_id}")
async def delete_satisfaction(record_id: int, db: Session = Depends(get_db)):
    """删除满意度记录"""
    db_record = db.query(Satisfaction).filter(Satisfaction.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(db_record)
    db.commit()
    return {"message": "记录已删除"}


# ============ Helpers ============

def _feedback_to_response(f: Feedback) -> FeedbackResponse:
    return FeedbackResponse(
        id=f.id,
        feedback_date=f.feedback_date or "",
        current_status=f.current_status or "",
        expected_result=f.expected_result or "",
        is_resolved=f.is_resolved or False,
        resolved_at=f.resolved_at,
        rating=f.rating,
        created_at=f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else "",
        updated_at=f.updated_at.strftime("%Y-%m-%d %H:%M:%S") if f.updated_at else ""
    )


def _sat_to_response(s: Satisfaction) -> SatisfactionResponse:
    return SatisfactionResponse(
        id=s.id,
        score=s.score,
        complaint=s.complaint or "",
        created_at=s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
        updated_at=s.updated_at.strftime("%Y-%m-%d %H:%M:%S") if s.updated_at else ""
    )
