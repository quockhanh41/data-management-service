import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import json
from typing import List
import re

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
                Chỉ trả về JSON, không có bất kỳ text nào khác.
                """
            elif language == 'en':
                prompt = f"""
                Analyze the following content and extract all main topics concisely, focusing only on the essence of the topics, removing details like "video", "article", "give me", etc.:
                "{user_input}"
                Return the result in JSON format:
                {{
                  "topics": ["topic 1", "topic 2", ...]
                }}
                Return only JSON, no other text.
                """
            else:
                prompt = f"""
                Analyze the following content and extract all main topics concisely, focusing only on the essence of the topics, removing details like "video", "article", "give me", etc.:
                "{user_input}"
                Return the result in JSON format:
                {{
                  "topics": ["topic 1", "topic 2", ...]
                }}
                Return only JSON, no other text.
                """
            
      
            # Sử dụng generation_config đúng cách
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
                   
            # Tìm JSON trong response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON found in response: {response.text}")
                return [user_input]
                
            json_str = json_match.group()
            logger.info(f"Extracted JSON: {json_str}")
            
            # Parse JSON response và trả về danh sách topics
            result = json.loads(json_str)
            if "topics" not in result:
                logger.error(f"Invalid JSON structure: {result}")
                return [user_input]
                
            return result["topics"]
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response text: {response.text}")
            return [user_input]
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
