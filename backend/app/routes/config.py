"""System configuration routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.salary import SystemConfig
from app.schemas.config import (
    SystemConfigCreate, SystemConfigUpdate,
    SystemConfigResponse, SystemConfigListResponse,
)
from app.authorization.dependencies import require
from app.authorization.permissions import Permission

router = APIRouter(prefix="/config", tags=["config"])

DEFAULT_CONFIGS = [
    {"key": "STANDARD_WORKING_HOURS", "value": "9.0", "description": "Standard working hours per day", "value_type": "float"},
    {"key": "OVERTIME_MULTIPLIER", "value": "1.5", "description": "Overtime pay multiplier (e.g., 1.5x)", "value_type": "float"},
    {"key": "DEDUCTION_RATE", "value": "1.0", "description": "Undertime deduction rate (1x hourly rate)", "value_type": "float"},
    {"key": "HALF_DAY_THRESHOLD_HOURS", "value": "6.0", "description": "Minimum hours for half-day", "value_type": "float"},
    {"key": "FULL_DAY_THRESHOLD_HOURS", "value": "9.0", "description": "Minimum hours for full day", "value_type": "float"},
    {"key": "LATE_ARRIVAL_GRACE_MINUTES", "value": "15", "description": "Grace period before marking late (minutes)", "value_type": "int"},
    {"key": "EARLY_EXIT_PENALTY_RATE", "value": "0.5", "description": "Penalty rate for early exit (hourly)", "value_type": "float"},
    {"key": "AUTO_CHECKOUT_HOURS", "value": "12.0", "description": "Hours after which to auto-checkout", "value_type": "float"},
    {"key": "MAX_OVERTIME_HOURS_PER_DAY", "value": "4.0", "description": "Maximum overtime hours per day", "value_type": "float"},
    {"key": "WEEKEND_DAYS", "value": "5,6", "description": "Weekend days (0=Mon, 6=Sun)", "value_type": "string"},
    {"key": "OFFICE_START_TIME", "value": "09:00", "description": "Standard office start time", "value_type": "string"},
    {"key": "OFFICE_END_TIME", "value": "18:00", "description": "Standard office end time", "value_type": "string"},
]


@router.get("/", response_model=SystemConfigListResponse)
def get_all_configs(
    current_user: User = Depends(require(Permission.VIEW_SYSTEM_CONFIG)),
    db: Session = Depends(get_db)
):
    """Get all system configurations."""
    configs = db.query(SystemConfig).order_by(SystemConfig.key).all()
    return SystemConfigListResponse(configs=configs, total=len(configs))


@router.get("/{key}", response_model=SystemConfigResponse)
def get_config(
    key: str,
    current_user: User = Depends(require(Permission.VIEW_SYSTEM_CONFIG)),
    db: Session = Depends(get_db)
):
    """Get a specific system configuration."""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Config '{key}' not found")
    return config


@router.put("/{key}", response_model=SystemConfigResponse)
def update_config(
    key: str,
    config_update: SystemConfigUpdate,
    current_user: User = Depends(require(Permission.MANAGE_SYSTEM_CONFIG)),
    db: Session = Depends(get_db)
):
    """Update a system configuration value."""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Config '{key}' not found")

    try:
        if config.value_type == "int":
            int(config_update.value)
        elif config.value_type == "float":
            float(config_update.value)
        elif config.value_type == "bool":
            if config_update.value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                raise ValueError("Invalid boolean value")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid value for type '{config.value_type}': {str(e)}")

    config.value = config_update.value
    if config_update.description is not None:
        config.description = config_update.description
    db.commit()
    db.refresh(config)
    return config


@router.post("/", response_model=SystemConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(
    config_create: SystemConfigCreate,
    current_user: User = Depends(require(Permission.MANAGE_SYSTEM_CONFIG)),
    db: Session = Depends(get_db)
):
    """Create a new system configuration."""
    existing = db.query(SystemConfig).filter(SystemConfig.key == config_create.key).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Config '{config_create.key}' already exists")

    config = SystemConfig(key=config_create.key, value=config_create.value, description=config_create.description, value_type=config_create.value_type)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    key: str,
    current_user: User = Depends(require(Permission.MANAGE_SYSTEM_CONFIG)),
    db: Session = Depends(get_db)
):
    """Delete a system configuration."""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Config '{key}' not found")
    db.delete(config)
    db.commit()
    return None


@router.post("/seed", response_model=SystemConfigListResponse)
def seed_default_configs(
    current_user: User = Depends(require(Permission.MANAGE_SYSTEM_CONFIG)),
    db: Session = Depends(get_db)
):
    """Seed default system configurations if they don't exist."""
    created = []
    for cfg in DEFAULT_CONFIGS:
        existing = db.query(SystemConfig).filter(SystemConfig.key == cfg["key"]).first()
        if not existing:
            config = SystemConfig(**cfg)
            db.add(config)
            created.append(config)

    db.commit()
    for cfg in created:
        db.refresh(cfg)

    all_configs = db.query(SystemConfig).order_by(SystemConfig.key).all()
    return SystemConfigListResponse(configs=all_configs, total=len(all_configs))
