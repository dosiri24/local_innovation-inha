"""
AI 채팅 모듈
사용자와의 자연스러운 대화를 통해 여행 니즈를 파악하고 요약하는 모듈
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
    """자연스러운 대화로 사용자 니즈를 파악하는 채팅봇"""
    
    def __init__(self):
        """ChatBot 초기화"""
        self.model = self._initialize_ai_model()
        self.conversation_history = []
        self.user_interests = []
        self.conversation_summary = ""
        
    def _initialize_ai_model(self):
        """Google Gemini AI 모델 초기화"""
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        print(f"[채팅봇] AI API 키 존재: {bool(api_key)}")
        
        if api_key and genai is not None:
            try:
                genai.configure(api_key=api_key)
                model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
                model = genai.GenerativeModel(model_name)
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
        """선택된 테마를 바탕으로 자연스러운 대화 시작"""
        self.user_interests = selected_themes
        
        themes_text = ', '.join(selected_themes) if selected_themes else '여행'
        
        start_prompt = f"""
        당신은 인천 제물포구의 친근한 현지 가이드입니다. 
        사용자가 '{themes_text}' 테마에 관심을 보였습니다.
        
        자연스럽고 친근하게 대화를 시작해주세요. 
        
        수집 권장 정보 (상황에 따라 유연하게):
        - 여행 동행자 (혼자/연인/가족/친구 등)
        - 관심 활동 (산책/쇼핑/맛집/역사탐방/체험 등)  
        - 선호 분위기 (조용히/활발하게/로맨틱/캐주얼 등)
        - 특별한 요청사항 (있다면)
        
        참고사항:
        - 모든 정보를 다 수집할 필요 없음
        - 2-3개 정보만 있어도 좋은 패스 생성 가능
        - 사용자가 간단히 답변하면 빠르게 마무리
        
        규칙:
        - 첫 인사는 간단하고 따뜻하게
        - 선택한 테마를 자연스럽게 언급
        - 구체적인 질문보다는 열린 질문으로 시작
        - 응답은 2-3문장 정도로 짧게
        - 제물포의 매력을 살짝 어필
        
        중요 - 부적절한 대화 감지:
        - 성적, 폭력적, 혐오 발언이 감지되면 대화를 즉시 중단
        - 정치적, 종교적 논쟁성 발언도 차단
        - 여행과 관련 없는 주제로 계속 전환 시도하면 경고 후 중단
        - 부적절한 내용 감지 시 정중하게 대화 종료 안내
        
        예시: "안녕하세요! 제물포에서 {themes_text} 여행을 계획하고 계시는군요. 이 동네는 정말 특별한 곳이 많아요! 어떤 분위기의 여행을 생각하고 계세요?"
        """
        
        try:
            if not self.model:
                raise Exception("AI 모델이 초기화되지 않았습니다.")
            
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
            raise Exception(f"대화 시작 중 오류가 발생했습니다: {str(e)}")

    def continue_conversation(self, user_message: str) -> Dict[str, Any]:
        """사용자 메시지를 받아 자연스럽게 대화 계속하기"""
        
        # 사용자 메시지 기록
        self.conversation_history.append({
            'type': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # 대화 히스토리 구성
        conversation_context = self._build_conversation_context()
        
        # 대화 단계 판단
        user_turns = len([msg for msg in self.conversation_history if msg['type'] == 'user'])
        
        prompt = f"""
        당신은 인천 제물포구 지역의 친근한 관광 가이드 '제물포GO'입니다.
        
        현재까지의 대화:
        {conversation_context}
        
        사용자의 최신 메시지: "{user_message}"
        현재 사용자 발언 횟수: {user_turns}번
        
        당신의 역할:
        1. 제물포 관광에 대해 친근하고 자연스럽게 대화하기
        2. 간단하고 핵심적인 정보만 수집하기 (너무 깊게 파지 않기)
        3. 적절한 시점에서 대화 마무리 판단하기
        4. 부적절한 대화 감지 시 즉시 대화 종료하기
        
        부적절한 대화 감지 및 대응:
        - 성적, 폭력적, 혐오적 내용이 포함된 경우
        - 정치적, 종교적 논쟁성 발언
        - 욕설, 비속어, 차별적 표현
        - 여행과 전혀 관련 없는 주제로 계속 전환하려는 시도
        - 개인정보 요구나 부적절한 만남 제안
        
        부적절한 대화 감지 시 응답:
        {{
            "message": "죄송합니다. 부적절한 내용이 감지되어 대화를 종료합니다. 제물포 여행 관련 대화만 가능합니다.",
            "finish": true,
            "inappropriate": true
        }}
        
        유동적 정보 수집 (상황에 따라 3-4개만 수집해도 충분):
        - 동행자 정보 (혼자, 연인, 가족, 친구 등)
        - 관심 활동이나 분위기 (산책, 역사탐방, 맛집, 쇼핑 등)
        - 간단한 선호도 (조용히/활발하게, 실내/야외 등)
        - 특별한 요구사항이 있다면
        
        대화 마무리 판단 기준:
        - 최소 4번의 대화 교환은 진행 (사용자 2번, 봇 2번 이상)
        - 동행자 + 관심사 3-4개 파악 후 요약 단계로 진입
        - 요약 제시 후 "더 하고 싶은 말이 있는지" 확인
        - 사용자가 "없다" 또는 "괜찮다"고 하면 그때 finish=true
        
        대화 진행 단계:
        1. 기본 정보 수집 (최소 4번 교환)
        2. 요약 제시 + 추가 의견 묻기 (1번)
        3. 사용자 확인 후 마무리 (1번)
        
        응답 규칙:
        - 1-2문장으로 짧고 친근하게 응답 필수
        - 사용자 발언 3번째부터는 요약 단계 진입 고려
        - 요약 시: "지금까지 말씀해주신 내용을 정리해보면... 더 추가하고 싶은 말씀이나 특별한 요청사항이 있으실까요?"
        - 요약 후 사용자 확인을 받으면 그때 finish=true
        
        정상 응답 형식:
        {{
            "message": "사용자에게 보낼 친근한 메시지",
            "finish": true/false
        }}
        
        부적절한 대화 감지 시 응답 형식:
        {{
            "message": "부적절한 내용 감지 안내 메시지",
            "finish": true,
            "inappropriate": true
        }}
        
        JSON 형식으로만 응답해주세요.
        """
        
        try:
            if not self.model:
                raise Exception("AI 모델이 초기화되지 않았습니다.")
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            result = json.loads(response_text)
            
            # 부적절한 대화 감지 확인
            is_inappropriate = result.get('inappropriate', False)
            if is_inappropriate:
                print(f"[채팅봇] 부적절한 대화 감지 - 사용자: {user_message[:50]}...")
                # 부적절한 대화 기록 (보안상 간단히)
                self.conversation_history.append({
                    'type': 'system',
                    'message': '부적절한 대화로 인한 종료',
                    'timestamp': datetime.now().isoformat()
                })
                
                return {
                    'message': result.get('message', '죄송합니다. 부적절한 내용이 감지되어 대화를 종료합니다.'),
                    'finish': True,
                    'inappropriate': True
                }
            
            # 봇 메시지 기록
            bot_message = result.get('message', '계속해서 이야기해주세요!')
            self.conversation_history.append({
                'type': 'bot',
                'message': bot_message,
                'timestamp': datetime.now().isoformat()
            })
            
            conversation_complete = result.get('finish', False)
            
            # 대화가 완료되면 요약 생성
            if conversation_complete:
                self.conversation_summary = self._generate_conversation_summary()
            
            print(f"[채팅봇] 대화 진행 - 완료여부: {conversation_complete}")
            
            return {
                'bot_message': bot_message,
                'conversation_complete': conversation_complete,
                'conversation_history': self.conversation_history.copy(),
                'conversation_summary': self.conversation_summary if conversation_complete else ""
            }
            
        except Exception as e:
            print(f"[채팅봇] 대화 처리 실패: {e}")
            raise Exception(f"대화 처리 중 오류가 발생했습니다: {str(e)}")

    def _build_conversation_context(self) -> str:
        """대화 히스토리를 텍스트로 구성"""
        context = []
        for entry in self.conversation_history[-8:]:  # 최근 8개 메시지만
            speaker = "가이드" if entry['type'] == 'bot' else "사용자"
            context.append(f"{speaker}: {entry['message']}")
        return '\n'.join(context)

    def _generate_conversation_summary(self) -> str:
        """대화 내용을 요약해서 패스 생성용 정보로 변환"""
        if not self.conversation_history:
            return "기본 여행 계획"
        
        # 전체 대화 내용 구성
        full_conversation = []
        for entry in self.conversation_history:
            speaker = "가이드" if entry['type'] == 'bot' else "사용자"
            full_conversation.append(f"{speaker}: {entry['message']}")
        
        conversation_text = '\n'.join(full_conversation)
        themes_text = ', '.join(self.user_interests) if self.user_interests else '일반 여행'
        
        summary_prompt = f"""
        다음은 제물포 여행에 대한 사용자와 가이드의 대화입니다.
        선택된 테마: {themes_text}
        
        대화 내용:
        {conversation_text}
        
        이 대화를 바탕으로 사용자의 여행 니즈를 종합적으로 요약해주세요.
        패스 생성 AI가 이해할 수 있도록 명확하고 구체적으로 작성해주세요.
        
        수집 가능한 정보들 (있는 것만 포함):
        - 동행자 정보 (관계, 인원수, 연령대, 특성)
        - 예산 범위와 소비 성향
        - 여행 시간대와 일정
        - 선호하는 이동 방식  
        - 식사 및 음료 선호도
        - 활동 스타일과 관심사
        - 특별한 요청사항이나 제약사항
        - 사용자의 성격이나 여행 철학
        
        중요: 대화에서 언급되지 않은 정보는 추측하지 말고 생략하세요.
        언급된 정보만으로도 충분히 좋은 패스를 생성할 수 있습니다.
        
        요약 형식:
        "사용자는 [확인된 동행자 정보]와 함께 [테마] 관련 여행을 원한다. [언급된 조건들]이며, [확인된 선호도들]을 보인다."
        
        2-3문장으로 대화에서 실제 언급된 내용만 간결하게 요약해주세요.
        """
        
        try:
            if not self.model:
                raise Exception("AI 모델이 초기화되지 않았습니다.")
            
            response = self.model.generate_content(summary_prompt)
            summary = response.text.strip()
            
            print(f"[채팅봇] 대화 요약 생성 완료: {summary[:50]}...")
            return summary
            
        except Exception as e:
            print(f"[채팅봇] 요약 생성 실패: {e}")
            raise Exception(f"대화 요약 생성 중 오류가 발생했습니다: {str(e)}")

    def get_conversation_summary(self) -> str:
        """대화 요약 반환 (패스 생성용)"""
        return self.conversation_summary

    def get_basic_preferences(self) -> Dict[str, Any]:
        """기본 선호도 정보 반환 (패스 생성용)"""
        return {
            'interests': self.user_interests,
            'conversation_summary': self.conversation_summary
        }

    def reset_conversation(self):
        """대화 초기화"""
        self.conversation_history = []
        self.user_interests = []
        self.conversation_summary = ""
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
