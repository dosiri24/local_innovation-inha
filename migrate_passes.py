#!/usr/bin/env python3
"""
기존 패스 파일들을 새로운 형식으로 업데이트하는 마이그레이션 스크립트
"""

import os
import json
from main import PASS_TYPES


def migrate_pass_files():
    """기존 패스 파일들을 새로운 형식으로 업데이트"""
    save_dir = "saved_passes"
    
    if not os.path.exists(save_dir):
        print("저장된 패스 파일이 없습니다.")
        return
    
    updated_count = 0
    
    # 모든 패스 파일 처리
    for filename in os.listdir(save_dir):
        if filename.startswith("pass_") and filename.endswith(".json"):
            file_path = os.path.join(save_dir, filename)
            
            try:
                # 기존 패스 데이터 로드
                with open(file_path, 'r', encoding='utf-8') as f:
                    pass_data = json.load(f)
                
                # 새로운 필드가 이미 있는지 확인
                if 'pass_info' in pass_data and 'user_input' in pass_data:
                    print(f"[건너뛰기] {filename} - 이미 업데이트됨")
                    continue
                
                # 패스 타입 정보 가져오기
                pass_type = pass_data.get('pass_type', 'light')
                pass_info = PASS_TYPES.get(pass_type, PASS_TYPES['light'])
                
                # pass_info 추가
                pass_data['pass_info'] = {
                    "name": pass_info.name,
                    "price": pass_info.price,
                    "description": pass_info.description,
                    "benefits_count": len(pass_data.get('recommendations', [])),
                    "total_value": pass_data.get('total_value', 0),
                    "value_ratio": round((pass_data.get('total_value', 0) / pass_info.price) * 100, 0) if pass_info.price > 0 else 0
                }
                
                # user_input 추가 (기본값)
                pass_data['user_input'] = {
                    "themes": ["전통", "카페"],  # 기본 테마
                    "request": "맛있는 음식과 분위기 좋은 카페를 찾고 있어요",  # 기본 요청
                    "pass_type": pass_type
                }
                
                # 사용자 이메일이 없으면 데모 이메일 설정
                if not pass_data.get('user_email'):
                    pass_data['user_email'] = 'demo@jemulpogo.com'
                
                # 업데이트된 데이터 저장
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(pass_data, f, ensure_ascii=False, indent=2)
                
                print(f"[업데이트] {filename}")
                updated_count += 1
                
            except Exception as e:
                print(f"[오류] {filename} 업데이트 실패: {e}")
    
    print(f"\n[완료] {updated_count}개 패스 파일이 업데이트되었습니다.")


if __name__ == "__main__":
    print("패스 파일 마이그레이션을 시작합니다...")
    migrate_pass_files()
