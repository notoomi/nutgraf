import openai
import anthropic
from .article_extractor import ArticleExtractor
import time

class LLMService:
    def __init__(self, user, provided_openai_key=None, provided_anthropic_key=None):
        self.user = user
        self.openai_client = None
        self.anthropic_client = None
        
        # Determine which API keys to use (provided keys take precedence)
        openai_key = provided_openai_key or user.get_openai_key()
        anthropic_key = provided_anthropic_key or user.get_anthropic_key()
        
        # Initialize clients based on available API keys
        if openai_key:
            try:
                self.openai_client = openai.OpenAI(
                    api_key=openai_key,
                    timeout=60.0,
                    max_retries=2
                )
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
        
        if anthropic_key:
            try:
                self.anthropic_client = anthropic.Anthropic(
                    api_key=anthropic_key,
                    timeout=60.0,
                    max_retries=2
                )
            except Exception as e:
                print(f"Failed to initialize Anthropic client: {e}")
    
    def generate_summary(self, content, length='standard', tone='neutral', 
                        format_type='prose', model='gpt-3.5-turbo', custom_word_count=None):
        """
        Generate a paraphrased summary of the given content
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(content, length, tone, format_type, custom_word_count)
            
            # Generate summary based on model
            if model.startswith('gpt'):
                if not self.openai_client:
                    raise Exception("OpenAI API key not configured")
                summary_text = self._generate_openai_summary(prompt, model)
            elif model.startswith('claude'):
                if not self.anthropic_client:
                    raise Exception("Anthropic API key not configured")
                summary_text = self._generate_anthropic_summary(prompt, model)
            else:
                raise Exception(f"Unsupported model: {model}")
            
            # Calculate word count
            word_count = len(summary_text.split())
            
            return {
                'text': summary_text,
                'word_count': word_count
            }
            
        except Exception as e:
            raise Exception(f"Summary generation failed: {str(e)}")
    
    def _build_prompt(self, content, length, tone, format_type, custom_word_count):
        """
        Build the prompt for summary generation
        """
        # Determine target word count
        word_count_map = {
            'brief': 100,
            'standard': 250,
            'in_depth': 500
        }
        
        target_words = custom_word_count if custom_word_count else word_count_map.get(length, 250)
        
        # Tone instructions
        tone_instructions = {
            'neutral': 'Use a neutral, objective tone.',
            'conversational': 'Use a conversational, friendly tone as if explaining to a colleague.',
            'professional': 'Use a formal, professional tone suitable for business contexts.'
        }
        
        # Format instructions
        format_instructions = {
            'prose': 'Write in continuous prose paragraphs.',
            'bullets': 'Use bullet points to organize the key information.'
        }
        
        # Build the main prompt
        prompt = f"""You are an expert at creating high-quality, paraphrased summaries of articles. Your task is to analyze the following article content and create a comprehensive summary that captures all salient facts and claims without using direct quotes.

INSTRUCTIONS:
- Target length: approximately {target_words} words
- {tone_instructions.get(tone, tone_instructions['neutral'])}
- {format_instructions.get(format_type, format_instructions['prose'])}
- Focus on factual information, key insights, and important claims
- Paraphrase everything - do not use direct quotes
- Maintain accuracy while making the content accessible
- Include specific numbers, dates, and concrete details when relevant
- Organize information logically and coherently

ARTICLE CONTENT:
{content}

SUMMARY:"""
        
        return prompt
    
    def _generate_openai_summary(self, prompt, model):
        """
        Generate summary using OpenAI models
        """
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not initialized. Please check your API key.")
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional article summarizer who creates accurate, paraphrased summaries without using direct quotes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                timeout=60.0
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("Empty response from OpenAI API")
            
            return response.choices[0].message.content.strip()
            
        except openai.AuthenticationError:
            raise Exception("Invalid OpenAI API key. Please check your API key in Settings.")
        except openai.RateLimitError:
            raise Exception("OpenAI rate limit exceeded. Please try again later.")
        except openai.APIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise Exception(f"OpenAI request failed: {str(e)}")
    
    def _generate_anthropic_summary(self, prompt, model):
        """
        Generate summary using Anthropic Claude models
        """
        try:
            if not self.anthropic_client:
                raise Exception("Anthropic client not initialized. Please check your API key.")
            
            # Map model names to Anthropic format
            model_map = {
                'claude-3-sonnet': 'claude-3-5-sonnet-20241022',
                'claude-3-haiku': 'claude-3-haiku-20240307',
                'claude-3-opus': 'claude-3-opus-20240229'
            }
            
            anthropic_model = model_map.get(model, 'claude-3-5-sonnet-20241022')
            
            response = self.anthropic_client.messages.create(
                model=anthropic_model,
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=60.0
            )
            
            if not response.content or not response.content[0].text:
                raise Exception("Empty response from Anthropic API")
            
            return response.content[0].text.strip()
            
        except anthropic.AuthenticationError:
            raise Exception("Invalid Anthropic API key. Please check your API key in Settings.")
        except anthropic.RateLimitError:
            raise Exception("Anthropic rate limit exceeded. Please try again later.")
        except anthropic.APIError as e:
            raise Exception(f"Anthropic API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Anthropic request failed: {str(e)}")
    
    def generate_summary_for_long_content(self, content, **kwargs):
        """
        Handle long content by chunking and summarizing
        """
        extractor = ArticleExtractor()
        chunks = extractor.chunk_content(content)
        
        if len(chunks) == 1:
            # Content fits in one chunk
            return self.generate_summary(content, **kwargs)
        
        # Multi-chunk processing
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            chunk_summary = self.generate_summary(
                chunk, 
                length='brief',  # Use brief for chunk summaries
                tone=kwargs.get('tone', 'neutral'),
                format_type='prose',
                model=kwargs.get('model', 'gpt-3.5-turbo')
            )
            chunk_summaries.append(chunk_summary['text'])
        
        # Combine chunk summaries
        combined_content = '\n\n'.join(chunk_summaries)
        
        # Generate final summary
        return self.generate_summary(combined_content, **kwargs)
    
    def get_available_models(self):
        """
        Get list of available models based on configured API keys
        """
        models = []
        
        if self.openai_client:
            models.extend([
                {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'provider': 'OpenAI'},
                {'id': 'gpt-4', 'name': 'GPT-4', 'provider': 'OpenAI'},
                {'id': 'gpt-4o', 'name': 'GPT-4o', 'provider': 'OpenAI'},
                {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo', 'provider': 'OpenAI'}
            ])
        
        if self.anthropic_client:
            models.extend([
                {'id': 'claude-3-haiku', 'name': 'Claude 3 Haiku', 'provider': 'Anthropic'},
                {'id': 'claude-3-sonnet', 'name': 'Claude 3.5 Sonnet', 'provider': 'Anthropic'},
                {'id': 'claude-3-opus', 'name': 'Claude 3 Opus', 'provider': 'Anthropic'}
            ])
        
        return models