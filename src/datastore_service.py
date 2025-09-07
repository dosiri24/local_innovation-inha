"""
Google Cloud Datastore를 사용한 패스 영구 저장
"""
import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
from models import Pass, Store, Benefit, UserPrefs, PassType, Theme

def is_production_environment():
    """프로덕션 환경 감지"""
    return (
        os.environ.get('GAE_ENV', '').startswith('standard') or 
        os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine/') or
        'appspot.com' in os.environ.get('GOOGLE_CLOUD_PROJECT', '')
    )

def get_datastore_client():
    """Google Cloud Datastore 클라이언트 가져오기"""
    try:
        if is_production_environment():
            from google.cloud import datastore
            return datastore.Client()
        else:
            print("[데이터스토어] 로컬 환경 - Datastore 사용하지 않음")
            return None
    except ImportError:
        print("[데이터스토어] google-cloud-datastore 라이브러리가 설치되지 않음")
        return None
    except Exception as e:
        print(f"[데이터스토어] 클라이언트 생성 실패: {e}")
        return None

def save_pass_to_datastore(pass_obj: Pass, user_email: str) -> bool:
    """패스를 Google Cloud Datastore에 저장"""
    try:
        client = get_datastore_client()
        if not client:
            print("[데이터스토어] 클라이언트 없음 - 저장 건너뜀")
            return False
        
        print(f"[데이터스토어] 패스 저장 시작: {pass_obj.pass_id}")
        
        # 패스 데이터를 직렬화 가능한 형태로 변환
        pass_data = {
            'pass_id': pass_obj.pass_id,
            'pass_type': pass_obj.pass_type.value,
            'theme': pass_obj.theme.value,
            'stores': [store.__dict__ for store in pass_obj.stores],
            'benefits': [benefit.__dict__ for benefit in pass_obj.benefits],
            'created_at': pass_obj.created_at,
            'user_prefs': pass_obj.user_prefs.__dict__,
            'user_email': user_email,
            'saved_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Datastore 엔티티 생성
        key = client.key('JemulpogoPass', pass_obj.pass_id)
        from google.cloud import datastore
        entity = datastore.Entity(key=key)
        
        # JSON을 Blob으로 저장 (크기 제한 없음)
        pass_data_json = json.dumps(pass_data, ensure_ascii=False)
        
        # JSON 크기 확인 (안전성)
        json_size = len(pass_data_json.encode('utf-8'))
        if json_size > 1000000:  # 1MB 제한
            print(f"[데이터스토어] 경고: 패스 데이터가 매우 큼 ({json_size} 바이트)")
        
        entity.update({
            'user_email': user_email,
            'pass_data_blob': pass_data_json.encode('utf-8'),  # Blob으로 저장
            'created_at': datetime.fromisoformat(pass_obj.created_at.replace('Z', '+00:00')) if isinstance(pass_obj.created_at, str) else pass_obj.created_at,
            'saved_at': datetime.now(timezone.utc),
            'pass_id': pass_obj.pass_id,
            'pass_type': pass_obj.pass_type.value,
            'theme': pass_obj.theme.value
        })
        
        # 저장
        client.put(entity)
        print(f"[데이터스토어] 패스 저장 완료: {pass_obj.pass_id}")
        return True
        
    except Exception as e:
        print(f"[데이터스토어] 패스 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_pass_from_datastore(pass_id: str) -> Optional[Pass]:
    """Google Cloud Datastore에서 패스 로드"""
    try:
        client = get_datastore_client()
        if not client:
            print("[데이터스토어] 클라이언트 없음 - 로드 건너뜀")
            return None
        
        print(f"[데이터스토어] 패스 로드 시작: {pass_id}")
        
        # 엔티티 조회
        key = client.key('JemulpogoPass', pass_id)
        entity = client.get(key)
        
        if not entity:
            print(f"[데이터스토어] 패스를 찾을 수 없음: {pass_id}")
            return None
        
        # Blob 데이터 파싱
        pass_data_blob = entity.get('pass_data_blob')
        if pass_data_blob:
            # 새 방식 (Blob)
            try:
                pass_data = json.loads(pass_data_blob.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as decode_error:
                print(f"[데이터스토어] Blob 데이터 파싱 실패: {decode_error}")
                return None
        else:
            # 이전 방식 (JSON 문자열) - 하위 호환성
            try:
                pass_data_json = entity.get('pass_data_json', '{}')
                pass_data = json.loads(pass_data_json)
            except json.JSONDecodeError as json_error:
                print(f"[데이터스토어] JSON 문자열 파싱 실패: {json_error}")
                return None
        
        if not pass_data:
            print(f"[데이터스토어] 패스 데이터가 비어있음: {pass_id}")
            return None
        
        # Pass 객체로 변환
        try:
            from services import _create_pass_from_data
            pass_obj = _create_pass_from_data(pass_data)
            
            if pass_obj:
                print(f"[데이터스토어] 패스 로드 완료: {pass_id}")
            else:
                print(f"[데이터스토어] 패스 객체 변환 실패: {pass_id}")
            return pass_obj
        except Exception as create_error:
            print(f"[데이터스토어] 패스 객체 생성 실패: {create_error}")
            return None
        
    except Exception as e:
        print(f"[데이터스토어] 패스 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_user_passes_from_datastore(user_email: str) -> List[Dict[str, Any]]:
    """사용자의 모든 패스를 Google Cloud Datastore에서 조회"""
    try:
        client = get_datastore_client()
        if not client:
            print("[데이터스토어] 클라이언트 없음 - 조회 건너뜀")
            return []
        
        print(f"[데이터스토어] 사용자 패스 조회: {user_email}")
        
        # 사용자 이메일로 패스 조회 (정렬 없이 - 인덱스 불필요)
        query = client.query(kind='JemulpogoPass')
        query.add_filter('user_email', '=', user_email)
        
        passes = []
        theme_names = {
            'food': '맛집', 'culture': '문화', 'shopping': '쇼핑',
            'entertainment': '오락', 'seafood': '해산물', 'cafe': '카페',
            'traditional': '전통', 'retro': '레트로', 'quiet': '조용함'
        }
        
        pass_type_names = {
            'light': '라이트', 'premium': '프리미엄', 'citizen': '시민'
        }
        
        pass_type_prices = {
            'light': 7900, 'premium': 14900, 'citizen': 6900
        }
        
        for entity in query.fetch():
            try:
                # Blob 데이터 파싱 (안전하게)
                pass_data_blob = entity.get('pass_data_blob')
                if pass_data_blob:
                    # 새 방식 (Blob)
                    try:
                        pass_data = json.loads(pass_data_blob.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError) as decode_error:
                        print(f"[데이터스토어] 패스 데이터 파싱 실패: {decode_error}")
                        continue
                else:
                    # 이전 방식 (JSON 문자열) - 하위 호환성
                    try:
                        pass_data_json = entity.get('pass_data_json', '{}')
                        pass_data = json.loads(pass_data_json)
                    except json.JSONDecodeError as json_error:
                        print(f"[데이터스토어] JSON 문자열 파싱 실패: {json_error}")
                        continue
                
                if not pass_data or not pass_data.get('pass_id'):
                    print("[데이터스토어] 유효하지 않은 패스 데이터, 건너뛰기")
                    continue
                
                theme_name = theme_names.get(pass_data.get('theme', '').lower(), pass_data.get('theme', '테마'))
                pass_type_name = pass_type_names.get(pass_data.get('pass_type', '').lower(), pass_data.get('pass_type', '타입'))
                pass_name = f"{theme_name} {pass_type_name} 패스"
                
                # 유효기간 계산 (안전하게)
                created_at = pass_data.get('created_at', datetime.now().isoformat())
                if isinstance(created_at, str):
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except (ValueError, TypeError) as date_error:
                        print(f"[데이터스토어] 날짜 파싱 실패: {date_error}, 현재 시간 사용")
                        created_date = datetime.now()
                else:
                    created_date = created_at if created_at else datetime.now()
                    
                # 유효기간은 30일
                try:
                    valid_until = created_date + timedelta(days=30)
                except TypeError:
                    print("[데이터스토어] 유효기간 계산 실패, 기본값 사용")
                    valid_until = datetime.now() + timedelta(days=30)
                
                # 패스 상태 결정
                now = datetime.now(timezone.utc) if created_date.tzinfo else datetime.now()
                status = 'expired' if now > valid_until else 'active'
                
                total_price = pass_type_prices.get(pass_data.get('pass_type', '').lower(), 7900)
                stores = pass_data.get('stores', [])
                benefits = pass_data.get('benefits', [])
                
                passes.append({
                    'pass_id': pass_data.get('pass_id'),
                    'name': pass_name,
                    'pass_type': pass_type_name,
                    'theme': theme_name,
                    'created_at': created_at,
                    'valid_until': valid_until.isoformat(),
                    'status': status,
                    'total_places': len(stores),
                    'visited_places': 0,
                    'total_price': total_price,
                    'store_count': len(stores),
                    'benefits_count': len(benefits),
                    'source': 'datastore'  # 출처 표시
                })
                
                print(f"[데이터스토어] 패스 추가: {pass_data.get('pass_id')}")
                
            except Exception as pass_error:
                print(f"[데이터스토어] 패스 처리 오류: {pass_error}")
                continue
        
        print(f"[데이터스토어] 총 {len(passes)}개 패스 조회됨")
        return passes
        
    except Exception as e:
        print(f"[데이터스토어] 사용자 패스 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return []

def delete_pass_from_datastore(pass_id: str) -> bool:
    """Google Cloud Datastore에서 패스 삭제"""
    try:
        client = get_datastore_client()
        if not client:
            return False
        
        key = client.key('JemulpogoPass', pass_id)
        client.delete(key)
        print(f"[데이터스토어] 패스 삭제 완료: {pass_id}")
        return True
        
    except Exception as e:
        print(f"[데이터스토어] 패스 삭제 실패: {e}")
        return False
