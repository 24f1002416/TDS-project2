"""
Quiz Solver: Handles quiz rendering, parsing, and solving
"""

import asyncio
import aiohttp
import json
import logging
import base64
from playwright.async_api import async_playwright
from openai import OpenAI
import time

logger = logging.getLogger(__name__)


class QuizSolver:
    def __init__(self, openai_api_key):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.max_time = 180  # 3 minutes in seconds

    async def render_page(self, url):
        """
        Render a JavaScript page using headless browser
        Returns the rendered HTML content
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # Navigate to the URL
                await page.goto(url, wait_until='networkidle', timeout=30000)

                # Wait for content to be rendered
                await page.wait_for_timeout(2000)

                # Get the rendered content
                content = await page.content()

                # Also get the text content for easier parsing
                text_content = await page.inner_text('body')

                await browser.close()

                return {
                    'html': content,
                    'text': text_content
                }
        except Exception as e:
            logger.error(f"Error rendering page {url}: {str(e)}")
            raise

    def parse_quiz_with_llm(self, page_content):
        """
        Use OpenAI to parse the quiz question and extract:
        - The question text
        - Any file URLs to download
        - The submit endpoint URL
        - The expected answer format
        """
        try:
            prompt = f"""
You are a quiz parser. Extract the following information from this quiz page:

1. The question being asked
2. Any URLs to download files (PDFs, CSVs, etc.)
3. The submit endpoint URL where answers should be posted
4. The expected format of the answer (boolean, number, string, object, base64, etc.)

Quiz page content:
{page_content['text']}

Return your response as a JSON object with keys: question, file_urls, submit_url, answer_format
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that parses quiz questions and extracts structured information."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Parsed quiz: {result}")
            return result

        except Exception as e:
            logger.error(f"Error parsing quiz with LLM: {str(e)}")
            raise

    async def download_file(self, url):
        """Download a file from URL and return its content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('Content-Type', '')
                        return {
                            'content': content,
                            'content_type': content_type
                        }
                    else:
                        raise Exception(f"Failed to download file: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading file {url}: {str(e)}")
            raise

    def solve_with_llm(self, quiz_info, file_data=None):
        """
        Use OpenAI to solve the quiz question
        Supports vision API for images and PDFs
        """
        try:
            messages = [
                {"role": "system", "content": "You are a data analysis expert. Answer questions about data accurately and concisely."}
            ]

            # Build the user message
            user_content = [
                {"type": "text", "text": f"Question: {quiz_info['question']}\n\nProvide only the answer in the format: {quiz_info.get('answer_format', 'appropriate format')}"}
            ]

            # If there's file data, include it
            if file_data:
                for file_info in file_data:
                    content_type = file_info['content_type']
                    content = file_info['content']

                    # For PDFs and images, use vision API
                    if 'pdf' in content_type.lower() or 'image' in content_type.lower():
                        base64_content = base64.b64encode(content).decode('utf-8')

                        if 'pdf' in content_type.lower():
                            # For PDFs, convert to images first or use text extraction
                            user_content.append({
                                "type": "text",
                                "text": f"[PDF file content - analyze the data within]"
                            })
                        else:
                            user_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type};base64,{base64_content}"
                                }
                            })

                    # For text-based files
                    elif 'text' in content_type.lower() or 'csv' in content_type.lower():
                        text_content = content.decode('utf-8')
                        user_content.append({
                            "type": "text",
                            "text": f"File content:\n{text_content}"
                        })

            messages.append({"role": "user", "content": user_content})

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=2000
            )

            answer_text = response.choices[0].message.content.strip()

            # Try to parse the answer into the appropriate format
            answer = self.format_answer(answer_text, quiz_info.get('answer_format'))

            logger.info(f"LLM answer: {answer}")
            return answer

        except Exception as e:
            logger.error(f"Error solving with LLM: {str(e)}")
            raise

    def format_answer(self, answer_text, answer_format):
        """
        Format the LLM's answer into the expected type
        """
        if not answer_format:
            return answer_text

        answer_format = answer_format.lower()

        try:
            if 'number' in answer_format or 'int' in answer_format:
                # Extract number from text
                import re
                numbers = re.findall(r'-?\d+\.?\d*', answer_text)
                if numbers:
                    return int(float(numbers[0]))

            elif 'boolean' in answer_format or 'bool' in answer_format:
                answer_lower = answer_text.lower()
                if 'true' in answer_lower or 'yes' in answer_lower:
                    return True
                elif 'false' in answer_lower or 'no' in answer_lower:
                    return False

            elif 'json' in answer_format or 'object' in answer_format:
                return json.loads(answer_text)
        except:
            pass

        # Default: return as string
        return answer_text

    async def submit_answer(self, submit_url, email, secret, quiz_url, answer):
        """
        Submit the answer to the quiz endpoint
        """
        try:
            payload = {
                "email": email,
                "secret": secret,
                "url": quiz_url,
                "answer": answer
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(submit_url, json=payload, timeout=30) as response:
                    result = await response.json()
                    logger.info(f"Submission result: {result}")
                    return result

        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}")
            raise

    async def solve_single_quiz(self, email, secret, url):
        """
        Solve a single quiz question
        Returns the response which may include the next URL
        """
        try:
            # Step 1: Render the page
            logger.info(f"Rendering quiz page: {url}")
            page_content = await self.render_page(url)

            # Step 2: Parse the quiz with LLM
            logger.info("Parsing quiz question")
            quiz_info = self.parse_quiz_with_llm(page_content)

            # Step 3: Download any required files
            file_data = []
            if quiz_info.get('file_urls'):
                logger.info(f"Downloading files: {quiz_info['file_urls']}")
                for file_url in quiz_info['file_urls']:
                    file_content = await self.download_file(file_url)
                    file_data.append(file_content)

            # Step 4: Solve the quiz with LLM
            logger.info("Solving quiz with LLM")
            answer = self.solve_with_llm(quiz_info, file_data)

            # Step 5: Submit the answer
            logger.info(f"Submitting answer: {answer}")
            submit_url = quiz_info.get('submit_url')
            result = await self.submit_answer(submit_url, email, secret, url, answer)

            return result

        except Exception as e:
            logger.error(f"Error solving quiz {url}: {str(e)}")
            raise

    async def solve_quiz_chain(self, email, secret, initial_url):
        """
        Solve a chain of quizzes, following the URLs returned by each submission
        """
        start_time = time.time()
        current_url = initial_url
        results = []

        while current_url and (time.time() - start_time) < self.max_time:
            try:
                logger.info(f"Solving quiz: {current_url}")
                result = await self.solve_single_quiz(email, secret, current_url)
                results.append(result)

                # Check if there's a next URL
                if result.get('correct'):
                    next_url = result.get('url')
                    if next_url:
                        logger.info(f"Moving to next quiz: {next_url}")
                        current_url = next_url
                    else:
                        logger.info("Quiz chain completed!")
                        break
                else:
                    # If incorrect, we can retry if we have time
                    reason = result.get('reason', 'Unknown error')
                    logger.warning(f"Answer was incorrect: {reason}")

                    # Check if there's a next URL to skip to
                    next_url = result.get('url')
                    if next_url:
                        logger.info(f"Skipping to next quiz: {next_url}")
                        current_url = next_url
                    else:
                        break

            except Exception as e:
                logger.error(f"Error in quiz chain: {str(e)}")
                break

        logger.info(f"Quiz chain completed. Total results: {len(results)}")
        return results
