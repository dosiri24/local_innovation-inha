"""
AI 채팅 모듈
사용자와의 대화를 통해 여행 니즈를 파악하는 모듈
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
try:
    import google.generativeai as genai
except ImportError:
    genai = None
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class ChatBot:
    """사용자 니즈 파악을 위한 채팅봇"""
    
    def __init__(self):
        """ChatBot 초기화"""
        self.model = self._initialize_ai_model()
        self.conversation_history = []
        self.user_interests = []
        self.extracted_info = {
            'themes': [],
            'budget': '보통',
            'group_size': 2,
            'duration': '반나절',
            'transportation': '도보',
            'special_requests': []
        }
        
    def _initialize_ai_model(self):
        """Google Gemini AI 모델 초기화"""
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        print(f"[채팅봇] AI API 키 존재: {bool(api_key)}")
        
        if api_key and genai is not None:
            try:
                genai.configure(api_key=api_key)  # type: ignore
                model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
                model = genai.GenerativeModel(model_name)  # type: ignore
                print(f"[채팅봇] Google Gemini 모델 '{model_name}' 초기화 완료")
                return model
            except Exception as e:
                print(f"[채팅봇] AI 모델 초기화 실패: {e}")
                return None
        else:
            if genai is None:
                print("[채팅봇] ❌ google-generativeai 패키지가 설치되지 않았습니다!")
            else:
                print("[채팅봇] ❌ GEMINI_API_KEY가 설정되지 않았습니다!")
            return None

    def start_conversation(self, selected_themes: List[str]) -> str:
        """선택된 테마를 바탕으로 대화 시작"""
        self.user_interests = selected_themes
        self.extracted_info['themes'] = selected_themes
        
        # 대화 시작 프롬프트
        themes_text = ', '.join(selected_themes) if selected_themes else '여행'
        
        start_prompt = f"""
        당신은 인천 제물포구 지역의 친근한 관광 가이드입니다. 
        사용자가 다음 테마에 관심을 보였습니다: {themes_text}
        
        사용자의 여행 계획을 자연스럽게 파악하기 위해 대화를 시작해주세요.
        
        다음 정보들을 자연스럽게 알아내야 합니다:
        - 예산 (저렴/보통/고급)
        - 함께 가는 사람 수
        - 여행 시간 (반나절/하루종일)
        - 이동 수단 (도보/대중교통/자동차)
        - 특별한 요청사항이나 선호도
        
        첫 인사말을 친근하고 자연스럽게 해주세요. 
        선택한 테마를 언급하면서 시작하되, 질문은 한 번에 하나씩만 해주세요.
        """
        
        try:
            if not self.model:
                return "안녕하세요! 제물포GO에 오신 것을 환영합니다. 선택하신 테마를 바탕으로 맞춤 여행을 계획해드릴게요!"
            
            response = self.model.generate_content(start_prompt)
            bot_message = response.text.strip()
            
            # 대화 기록에 추가
            self.conversation_history.append({
                'type': 'bot',
                'message': bot_message,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"[채팅봇] 대화 시작: {themes_text} 테마")
            return bot_message
            
        except Exception as e:
            print(f"[채팅봇] 대화 시작 실패: {e}")
            return f"안녕하세요! {themes_text} 테마로 멋진 제물포 여행을 계획해보세요! 어떤 분위기의 여행을 원하시나요?"

    def continue_conversation(self, user_message: str) -> Dict[str, Any]:
        """사용자 메시지를 받아 대화 계속하기"""
        
        # 사용자 메시지 기록
        self.conversation_history.append({
            'type': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # 대화 히스토리 구성
        conversation_context = self._build_conversation_context()
        
        # AI 응답 생성
        prompt = f"""
        당신은 인천 제물포구 지역의 친근한 관광 가이드입니다.
        
        현재까지의 대화:
        {conversation_context}
        
        사용자의 최신 메시지: "{user_message}"
        
        다음 정보들을 자연스럽게 파악해야 합니다:
        - 예산 (저렴/보통/고급)
        - 함께 가는 사람 수
        - 여행 시간 (반나절/하루종일)  
        - 이동 수단 (도보/대중교통/자동차)
        - 특별한 요청사항이나 선호도
        
        현재 파악된 정보:
        - 관심 테마: {', '.join(self.user_interests)}
        - 예산: {self.extracted_info.get('budget', '미파악')}
        - 인원: {self.extracted_info.get('group_size', '미파악')}
        - 시간: {self.extracted_info.get('duration', '미파악')}
        - 교통: {self.extracted_info.get('transportation', '미파악')}
        
        규칙:
        1. 친근하고 자연스럽게 대화하세요
        2. 질문은 한 번에 하나씩만 하세요
        3. 아직 파악하지 못한 정보가 있으면 자연스럽게 물어보세요
        4. 충분한 정보가 모이면 "정보 수집 완료"를 언급하세요
        5. 제물포구 지역의 매력을 어필하세요
        
        응답 형식:
        {{
            "bot_message": "사용자에게 보낼 메시지",
            "extracted_info": {{
                "budget": "저렴/보통/고급 중 하나 또는 null",
                "group_size": 숫자 또는 null,
                "duration": "반나절/하루종일 중 하나 또는 null",
                "transportation": "도보/대중교통/자동차 중 하나 또는 null",
                "special_requests": ["파악된 특별 요청사항들"]
            }},
            "conversation_complete": true/false
        }}
        
        JSON 형식으로만 응답해주세요.
        """
        
        try:
            if not self.model:
                return self._fallback_response(user_message)
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            result = json.loads(response_text)
            
            # 추출된 정보 업데이트
            extracted = result.get('extracted_info', {})
            for key, value in extracted.items():
                if value is not None:
                    if key == 'special_requests':
                        self.extracted_info[key].extend(value)
                    else:
                        self.extracted_info[key] = value
            
            # 봇 메시지 기록
            bot_message = result.get('bot_message', '계속해서 이야기해주세요!')
            self.conversation_history.append({
                'type': 'bot',
                'message': bot_message,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"[채팅봇] 정보 업데이트: {self.extracted_info}")
            
            return {
                'bot_message': bot_message,
                'extracted_info': self.extracted_info.copy(),
                'conversation_complete': result.get('conversation_complete', False),
                'conversation_history': self.conversation_history.copy()
            }
            
        except Exception as e:
            print(f"[채팅봇] 대화 처리 실패: {e}")
            return self._fallback_response(user_message)

    def _build_conversation_context(self) -> str:
        """대화 히스토리를 텍스트로 구성"""
        context = []
        for entry in self.conversation_history[-6:]:  # 최근 6개 메시지만
            speaker = "가이드" if entry['type'] == 'bot' else "사용자"
            context.append(f"{speaker}: {entry['message']}")
        return '\n'.join(context)

    def _fallback_response(self, user_message: str) -> Dict[str, Any]:
        """AI 호출 실패시 폴백 응답"""
        
        # 간단한 키워드 기반 정보 추출
        extracted = {}
        
        # 예산 관련 키워드
        if any(word in user_message for word in ['저렴', '싸게', '절약', '가성비']):
            extracted['budget'] = '저렴'
        elif any(word in user_message for word in ['고급', '비싸게', '럭셔리', '프리미엄']):
            extracted['budget'] = '고급'
        elif any(word in user_message for word in ['적당', '보통', '평범']):
            extracted['budget'] = '보통'
            
        # 인원 관련 키워드
        numbers = ['혼자', '둘이', '셋이', '넷이', '다섯']
        for i, num_word in enumerate(numbers):
            if num_word in user_message:
                extracted['group_size'] = i + 1
                break
        
        # 시간 관련 키워드  
        if any(word in user_message for word in ['하루', '하루종일', '오래']):
            extracted['duration'] = '하루종일'
        elif any(word in user_message for word in ['반나절', '짧게', '잠깐']):
            extracted['duration'] = '반나절'
            
        # 교통 관련 키워드
        if any(word in user_message for word in ['걸어', '도보', '산책']):
            extracted['transportation'] = '도보'
        elif any(word in user_message for word in ['차', '자동차', '드라이브']):
            extracted['transportation'] = '자동차'
        elif any(word in user_message for word in ['버스', '지하철', '대중교통']):
            extracted['transportation'] = '대중교통'
        
        # 추출된 정보 업데이트
        for key, value in extracted.items():
            self.extracted_info[key] = value
        
        # 간단한 응답 생성
        missing_info = []
        if not self.extracted_info.get('budget') or self.extracted_info['budget'] == '보통':
            missing_info.append('예산')
        if not self.extracted_info.get('group_size') or self.extracted_info['group_size'] == 2:
            missing_info.append('인원수')
        if not self.extracted_info.get('duration') or self.extracted_info['duration'] == '반나절':
            missing_info.append('여행시간')
        if not self.extracted_info.get('transportation') or self.extracted_info['transportation'] == '도보':
            missing_info.append('이동수단')
        
        if missing_info:
            bot_message = f"네, 알겠습니다! 혹시 {missing_info[0]}은 어떻게 생각하고 계신가요?"
        else:
            bot_message = "완벽해요! 이제 멋진 제물포 여행 패스를 만들어드릴게요!"
        
        self.conversation_history.append({
            'type': 'bot',
            'message': bot_message,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'bot_message': bot_message,
            'extracted_info': self.extracted_info.copy(),
            'conversation_complete': len(missing_info) == 0,
            'conversation_history': self.conversation_history.copy()
        }

    def get_final_preferences(self) -> Dict[str, Any]:
        """최종 사용자 선호도 반환 (패스 생성용)"""
        return {
            'budget': self.extracted_info.get('budget', '보통'),
            'interests': self.user_interests,
            'dietary_restrictions': [],
            'group_size': self.extracted_info.get('group_size', 2),
            'duration': self.extracted_info.get('duration', '반나절'),
            'transportation': self.extracted_info.get('transportation', '도보'),
            'special_requests': self.extracted_info.get('special_requests', [])
        }

    def reset_conversation(self):
        """대화 초기화"""
        self.conversation_history = []
        self.user_interests = []
        self.extracted_info = {
            'themes': [],
            'budget': '보통',
            'group_size': 2,
            'duration': '반나절',
            'transportation': '도보',
            'special_requests': []
        }
        print("[채팅봇] 대화 초기화 완료")


# 전역 채팅봇 인스턴스 관리
_chatbot_sessions = {}

def get_chatbot(session_id: str) -> ChatBot:
    """세션별 채팅봇 인스턴스 반환"""
    if session_id not in _chatbot_sessions:
        _chatbot_sessions[session_id] = ChatBot()
    return _chatbot_sessions[session_id]

def clear_chatbot_session(session_id: str):
    """채팅봇 세션 삭제"""
    if session_id in _chatbot_sessions:
        del _chatbot_sessions[session_id]
        print(f"[채팅봇] 세션 {session_id} 삭제")
