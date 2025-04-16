import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import json
from typing import List

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def extract_topic(self, user_input: str, language: str) -> List[str]:
        try:
            # Tạo prompt phù hợp với ngôn ngữ
            if language == 'vi':
                prompt = f"""
                Phân tích nội dung sau và trích xuất tất cả các chủ đề chính (topics) một cách ngắn gọn, chỉ bao gồm bản chất của chủ đề, loại bỏ các chi tiết như "video", "bài viết", "cho tôi", v.v.:
                "{user_input}"
                Kết quả trả về theo định dạng JSON:
                {{
                  "topics": ["chủ đề 1", "chủ đề 2", ...]
                }}
                """
            elif language == 'en':
                prompt = f"""
                Analyze the following content and extract all main topics concisely, focusing only on the essence of the topics, removing details like "video", "article", "give me", etc.:
                "{user_input}"
                Return the result in JSON format:
                {{
                  "topics": ["topic 1", "topic 2", ...]
                }}
                """
            else:
                prompt = f"""
                Analyze the following content and extract all main topics concisely, focusing only on the essence of the topics, removing details like "video", "article", "give me", etc.:
                "{user_input}"
                Return the result in JSON format:
                {{
                  "topics": ["topic 1", "topic 2", ...]
                }}
                """
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse JSON response và trả về danh sách topics
            result = json.loads(response.text)
            return result["topics"]
        except Exception as e:
            logger.error(f"Error extracting topics with Gemini: {str(e)}")
            return [user_input]  # Trả về input gốc trong một list nếu có lỗi 
        
# test
if __name__ == "__main__":
    import asyncio

    async def main():
        gemini_service = GeminiService()
        topic = await gemini_service.extract_topic("Tôi muốn tìm hiểu về các chủ đề liên quan đến khoa học máy tính và công nghệ thông tin", "vi")
        print(topic)
    
    asyncio.run(main())
