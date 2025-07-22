"""
配置管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time
from typing import List

from ..database import get_db
from ..models import APIConfig
from ..schemas import APIConfigCreate, APIConfigResponse, APITestRequest, APITestResponse
from ..services.config_service import ConfigService

router = APIRouter()

@router.post("/api", response_model=APIConfigResponse)
def create_api_config(
    config_data: APIConfigCreate,
    db: Session = Depends(get_db)
):
    """
    创建API配置
    """
    # 如果设置为默认配置，先取消其他默认配置
    if config_data.is_default:
        db.query(APIConfig).update({"is_default": False})
    
    # 加密API密钥
    encrypted_key = ConfigService.encrypt_api_key(config_data.api_key)
    
    # 创建配置
    config = APIConfig(
        name=config_data.name,
        endpoint=config_data.endpoint,
        api_key_encrypted=encrypted_key,
        model=config_data.model,
        is_default=config_data.is_default
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    # 返回时添加掩码显示的API密钥
    response_data = APIConfigResponse.from_orm(config)
    response_data.api_key_masked = ConfigService.mask_api_key(config_data.api_key)
    
    return response_data

@router.get("/api/{config_id}", response_model=APIConfigResponse)
def get_api_config(config_id: int, db: Session = Depends(get_db)):
    """
    获取API配置详情
    """
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 解密API密钥用于掩码显示
    try:
        decrypted_key = ConfigService.decrypt_api_key(config.api_key_encrypted)
        response_data = APIConfigResponse.from_orm(config)
        response_data.api_key_masked = ConfigService.mask_api_key(decrypted_key)
        return response_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置解密失败"
        )

@router.get("/api", response_model=List[APIConfigResponse])
def list_api_configs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取API配置列表
    """
    configs = db.query(APIConfig).filter(APIConfig.is_active == True).offset(skip).limit(limit).all()
    
    results = []
    for config in configs:
        try:
            decrypted_key = ConfigService.decrypt_api_key(config.api_key_encrypted)
            response_data = APIConfigResponse.from_orm(config)
            response_data.api_key_masked = ConfigService.mask_api_key(decrypted_key)
            results.append(response_data)
        except Exception:
            # 如果解密失败，跳过这个配置
            continue
    
    return results

@router.put("/api/{config_id}", response_model=APIConfigResponse)
def update_api_config(
    config_id: int,
    config_update: APIConfigCreate,
    db: Session = Depends(get_db)
):
    """
    更新API配置
    """
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    # 如果设置为默认配置，先取消其他默认配置
    if config_update.is_default:
        db.query(APIConfig).update({"is_default": False})
    
    # 更新字段
    config.name = config_update.name
    config.endpoint = config_update.endpoint
    config.model = config_update.model
    config.is_default = config_update.is_default
    
    # 如果提供了新的API密钥，更新加密后的密钥
    if config_update.api_key:
        config.api_key_encrypted = ConfigService.encrypt_api_key(config_update.api_key)
    
    db.commit()
    db.refresh(config)
    
    # 返回时添加掩码显示的API密钥
    decrypted_key = ConfigService.decrypt_api_key(config.api_key_encrypted)
    response_data = APIConfigResponse.from_orm(config)
    response_data.api_key_masked = ConfigService.mask_api_key(decrypted_key)
    
    return response_data

@router.delete("/api/{config_id}")
def delete_api_config(config_id: int, db: Session = Depends(get_db)):
    """
    删除API配置（软删除）
    """
    config = db.query(APIConfig).filter(APIConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    config.is_active = False
    db.commit()
    
    return {"message": "配置删除成功"}

@router.post("/api/test", response_model=APITestResponse)
async def test_api_connection(test_data: APITestRequest):
    """
    测试API连接
    """
    try:
        start_time = time.time()
        
        # 这里应该调用实际的AI客户端进行测试
        # 暂时返回模拟结果
        success, message = await ConfigService.test_api_connection(
            endpoint=test_data.endpoint,
            api_key=test_data.api_key,
            model=test_data.model
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return APITestResponse(
            success=success,
            message=message,
            latency_ms=latency_ms
        )
        
    except Exception as e:
        return APITestResponse(
            success=False,
            message=f"连接测试失败: {str(e)}"
        )

@router.get("/api/default", response_model=APIConfigResponse)
def get_default_api_config(db: Session = Depends(get_db)):
    """
    获取默认API配置
    """
    config = db.query(APIConfig).filter(
        APIConfig.is_default == True,
        APIConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未设置默认API配置"
        )
    
    decrypted_key = ConfigService.decrypt_api_key(config.api_key_encrypted)
    response_data = APIConfigResponse.from_orm(config)
    response_data.api_key_masked = ConfigService.mask_api_key(decrypted_key)
    
    return response_data