"""
Kakao Talk Channel API 통합
"""

import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class KakaoService:
    def __init__(self):
        self.api_url = "https://kapi.kakao.com"
        self.rest_api_key = settings.KAKAO_REST_API_KEY
        self.channel_id = settings.KAKAO_CHANNEL_ID

    async def send_message(
        self,
        user_id: str,
        message: str
    ) -> bool:
        """
        Kakao Talk 채널 메시지 전송

        Args:
            user_id: 사용자 Kakao ID
            message: 메시지 내용

        Returns:
            성공 여부
        """

        try:
            headers = {
                "Authorization": f"KakaoAK {self.rest_api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "receiver_id": user_id,
                "template_object": {
                    "object_type": "text",
                    "text": message,
                    "link": {
                        "web_url": "http://localhost:3000/dashboard"
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/v2/api/talk/memo/default/send",
                    headers=headers,
                    json=data
                )

                if response.status_code != 200:
                    logger.error(
                        f"Kakao API error: {response.status_code} - "
                        f"{response.text}"
                    )
                    return False

                logger.info(f"Kakao message sent to user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to send Kakao message: {str(e)}")
            return False
