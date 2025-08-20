"""
데이터 모델 정의
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

@dataclass
class Store:
    """상점 정보"""
    name: str
    category: str
    address: str
    phone: str
    description: str
    rating: float
    price_range: str
    opening_hours: str
    menu_highlights: List[str]
    location: str
    image_url: str = ""

@dataclass
class Benefit:
    """혜택 정보"""
    store_name: str
    benefit_type: str
    description: str
    discount_rate: Optional[str] = None
    valid_until: Optional[str] = None
    terms: Optional[str] = None

@dataclass
class UserPrefs:
    """사용자 선호도"""
    budget: str
    interests: List[str]
    dietary_restrictions: List[str]
    group_size: int
    duration: str
    transportation: str
    
class PassType(Enum):
    """패스 타입"""
    LIGHT = "light"
    PREMIUM = "premium"
    CITIZEN = "citizen"
    TASTE = "맛있는 동인천"
    BEAUTY = "아름다운 동인천"
    
class Theme(Enum):
    """테마"""
    FOOD = "음식"
    CULTURE = "문화"
    SHOPPING = "쇼핑"
    ENTERTAINMENT = "엔터테인먼트"
    SEAFOOD = "해산물"
    CAFE = "카페"
    TRADITIONAL = "전통"
    RETRO = "레트로"
    QUIET = "조용함"

@dataclass
class Pass:
    """패스 정보"""
    pass_id: str
    pass_type: PassType
    theme: Theme
    stores: List[Store]
    benefits: List[Benefit]
    created_at: str
    user_prefs: UserPrefs
    qr_code_path: Optional[str] = None
