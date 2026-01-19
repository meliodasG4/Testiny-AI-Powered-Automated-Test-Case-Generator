import json
import google.generativeai as genai
import time
from typing import Dict, List, Any, Optional
import re
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

class Config:
    """Configuration class"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = "models/gemini-2.5-flash"
    MIN_TEST_CASES = 20
    CHUNK_SIZE = 10000  # Characters per chunk
    CHUNK_OVERLAP = 500  # Overlap between chunks

class PDFProcessor:
    """Handle PDF loading and chunking"""
    
    def __init__(self, chunk_size: int = 10000, chunk_overlap: int = 500):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_pdf(self, pdf_path: str) -> str:
        """Load PDF and extract text using PyPDF2"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        except Exception as e:
            raise Exception(f"Error loading PDF: {str(e)}")
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        
        return chunks

class RAGRetriever:
    """Simple RAG retriever using Gemini embeddings"""
    
    def __init__(self, model: genai.GenerativeModel):
        self.model = model
        self.chunks = []
        self.chunk_embeddings = []
    
    def index_documents(self, chunks: List[str]):
        """Index document chunks (simplified - uses first few chunks)"""
        self.chunks = chunks
        print(f"    Indexed {len(chunks)} document chunks")
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve most relevant chunks (simplified - returns first chunks)"""
        # Simple retrieval: return first chunks as context
        # In production, you'd use embeddings and similarity search
        return self.chunks[:top_k]

class GeminiTestGenerator:  
    """Test generator with RAG support"""
    
    def __init__(self, api_key: str = None, model: str = None, pdf_paths: List[str] = None):
        """Initialize with optional PDF documents"""
        self.config = Config()
        
        pdf_paths= pdf_paths or ["blackbox-07.pdf"]
        api_key = api_key or self.config.GEMINI_API_KEY
        model = model or self.config.GEMINI_MODEL
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
            }
        )
        
        self.model_name = model
        
        # Initialize RAG components
        self.pdf_processor = PDFProcessor(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP
        )
        self.rag_retriever = RAGRetriever(self.model)
        self.knowledge_base = ""
        
        # Load PDFs if provided
        if pdf_paths:
            self.load_pdf_documents(pdf_paths)
    
    
    
    def load_pdf_documents(self, pdf_paths: List[str]):
        """Load and index PDF documents"""
        print("\n Loading PDF documents...")
        all_text = ""
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"    ⚠️  Warning: PDF not found: {pdf_path}")
                continue
            
            print(f"    Loading: {Path(pdf_path).name}")
            try:
                text = self.pdf_processor.load_pdf(pdf_path)
                all_text += text + "\n\n"
                print(f"    ✓ Loaded {len(text)} characters")
            except Exception as e:
                print(f"    ✗ Error loading {pdf_path}: {str(e)}")
        
        if all_text:
            # Chunk the combined text
            chunks = self.pdf_processor.chunk_text(all_text)
            self.rag_retriever.index_documents(chunks)
            self.knowledge_base = all_text[:20000]  # Store first 20k chars for quick access
            print(f"    ✓ RAG knowledge base ready with {len(chunks)} chunks\n")
        else:
            print("      No PDF content loaded\n")
    
    def add_pdf_document(self, pdf_path: str):
        """Add a single PDF document to the knowledge base"""
        self.load_pdf_documents([pdf_path])
    
    def generate_test_cases(self, web_data: Dict, user_stories: List[str] = None) -> Dict:
        """Generate main test cases with RAG context"""
        # Retrieve relevant context from PDFs
        context = ""
        if self.knowledge_base:
            query = f"test cases for {web_data.get('basic_info', {}).get('url', 'web application')}"
            relevant_chunks = self.rag_retriever.retrieve_relevant_chunks(query, top_k=2)
            context = "\n\n".join(relevant_chunks)
        
        prompt = self._build_main_prompt(web_data, user_stories, context)
        
        try:
            response = self.model.generate_content(prompt)
            test_cases = self._parse_response(response.text)
            
            test_cases['metadata'] = {
                'generated_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                'model_used': self.model_name,
                'ai_generated': True,
                'rag_enabled': bool(self.knowledge_base)
            }
            
            return test_cases
            
        except Exception as e:
            print(f"    Error generating test cases: {str(e)}")
            return self._get_fallback_tests(web_data)
    
    def generate_test_suites(self, web_data: Dict) -> Dict:
        """Generate 4 specialized test suites with RAG context"""
        print("    Generating test suites with AI...")
        
        suites = {}
        
        # Get relevant context once for all suites
        context = ""
        if self.knowledge_base:
            query = f"test suites for {web_data.get('basic_info', {}).get('url', 'web application')}"
            relevant_chunks = self.rag_retriever.retrieve_relevant_chunks(query, top_k=2)
            context = "\n\n".join(relevant_chunks)
        
        # Suite 1: Performance Tests
        print("    Generating Performance Test Suite...")
        suites['performance'] = self._generate_suite(
            web_data, 
            "performance",
            "Generate 4 performance test cases focusing on: page load time, API response time, resource optimization, caching, database performance",
            context
        )
        
        # Suite 2: Cross-Browser Tests
        print("    Generating Cross-Browser Test Suite...")
        suites['cross_browser'] = self._generate_suite(
            web_data,
            "cross_browser",
            "Generate 4 cross-browser compatibility test cases for Chrome, Firefox, Edge. Focus on: rendering consistency, JavaScript compatibility, CSS support",
            context
        )
        
        # Suite 3: Responsive Design Tests
        print("    Generating Responsive Design Test Suite...")
        suites['responsive_design'] = self._generate_suite(
            web_data,
            "responsive_design",
            "Generate 4 responsive design test cases for resolutions: 1920x1080, 1366x768, 768x1024, 375x667, 320x568. Focus on: layout adaptation, touch targets, font scaling",
            context
        )
        
        # Suite 4: Stress Tests
        print("    ⚡ Generating Stress Test Suite...")
        suites['stress'] = self._generate_suite(
            web_data,
            "stress",
            "Generate 4 stress test cases focusing on: high concurrent users, memory usage, network latency, long duration testing, database load",
            context
        )
        
        return suites
    
    def generate_all_tests(self, web_data: Dict, user_stories: List[str] = None):
        """
        Generate both main test cases and all test suites
        Returns everything in one call - perfect for UI integration
        """
        print("\n" + "="*60)
        print(" GENERATING ALL TESTS WITH AI")
        print("="*60)
        
        # Generate main test cases
        print("\n Generating Main Test Cases...")
        main_test_cases = self.generate_test_cases(web_data, user_stories)
        print(f"    Generated {len(main_test_cases.get('test_cases', []))} main test cases")
        
        # Generate test suites
        print("\n📦 Generating Test Suites...")
        test_suites = self.generate_test_suites(web_data)
        print("    All test suites generated")
        
        return {
            "main_test_cases": main_test_cases,
            "test_suites": test_suites,
            "web_data": web_data
        }
    
    def _generate_suite(self, web_data: Dict, suite_type: str, instructions: str, context: str = "") -> List[Dict]:
        """Generate a specific test suite with RAG context"""
        
        context_section = ""
        if context:
            context_section = f"""
REFERENCE DOCUMENTATION:
{context[:3000]}

Use the above documentation to inform your test cases.
"""
        
        prompt = f"""Generate 4 {suite_type.replace('_', ' ')} test cases for this website:
        
{json.dumps(web_data, indent=2)}

{context_section}

{instructions}

Output format - MUST BE VALID JSON ARRAY:
[
  {{
    "id": "PERF-001",
    "name": "Test name",
    "description": "Test description",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "expected_result": "Expected outcome",
    "priority": "high"
  }}
]"""
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_suite_response(response.text, suite_type)
        except Exception as e:
            print(f"    AI failed for {suite_type}, using default tests")
            return self._get_default_suite_tests(web_data, suite_type)
    
    def _parse_suite_response(self, response_text: str, suite_type: str) -> List[Dict]:
        """Parse suite response"""
        try:
            text = response_text.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            json_match = re.search(r'(\[.*\])', text, re.DOTALL)
            if json_match:
                tests = json.loads(json_match.group(1))
                for test in tests:
                    test.setdefault('id', f"{suite_type.upper()[:4]}-{len(tests)}")
                    test.setdefault('suite_type', suite_type)
                return tests
            return []
        except:
            return []
    
    def _get_default_suite_tests(self, web_data: Dict, suite_type: str) -> List[Dict]:
        """Default test suites if AI fails"""
        base_url = web_data.get('basic_info', {}).get('url', 'https://example.com')
        
        default_suites = {
            'performance': [
                {
                    "id": "PERF-001",
                    "name": "Page Load Time Measurement",
                    "description": "Measure initial page load time",
                    "steps": [
                        f"1. Clear browser cache",
                        f"2. Navigate to {base_url}",
                        "3. Start timer on navigation",
                        "4. Stop timer when page fully loads",
                        "5. Record load time"
                    ],
                    "expected_result": "Page loads within 3000ms",
                    "priority": "high",
                    "suite_type": "performance"
                }
            ],
            'cross_browser': [
                {
                    "id": "BROWSER-001",
                    "name": "Chrome Compatibility Test",
                    "description": "Verify all features work in Google Chrome",
                    "steps": [
                        "1. Open Chrome browser (latest version)",
                        f"2. Navigate to {base_url}",
                        "3. Test all interactive elements"
                    ],
                    "expected_result": "All features work correctly in Chrome",
                    "priority": "high",
                    "suite_type": "cross_browser"
                }
            ],
            'responsive_design': [
                {
                    "id": "RESP-001",
                    "name": "Desktop Resolution Test (1920x1080)",
                    "description": "Test at full HD desktop resolution",
                    "steps": [
                        "1. Set browser window to 1920x1080",
                        f"2. Navigate to {base_url}",
                        "3. Verify layout uses full width appropriately"
                    ],
                    "expected_result": "Layout optimized for desktop",
                    "priority": "medium",
                    "suite_type": "responsive_design"
                }
            ],
            'stress': [
                {
                    "id": "STRESS-001",
                    "name": "Concurrent User Load Test",
                    "description": "Simulate multiple concurrent users",
                    "steps": [
                        f"1. Setup load testing tool for {base_url}",
                        "2. Configure 50 virtual users",
                        "3. Run test for 5 minutes"
                    ],
                    "expected_result": "System handles 50 concurrent users",
                    "priority": "high",
                    "suite_type": "stress"
                }
            ]
        }
        
        return default_suites.get(suite_type, [])
    
    def _build_main_prompt(self, web_data: Dict, user_stories: List[str], context: str = "") -> str:
        """Build prompt for main test cases with RAG context"""
        
        context_section = ""
        if context:
            context_section = f"""
REFERENCE DOCUMENTATION FROM PDF:
{context[:5000]}

Use the above documentation as reference when creating test cases.
"""
        
        user_stories_section = ""
        if user_stories:
            user_stories_section = f"""
USER STORIES:
{json.dumps(user_stories, indent=2)}
"""
        
        return f"""Generate 20 test cases for this web application:

{json.dumps(web_data, indent=2)}

{context_section}

{user_stories_section}

Requirements:
- 10 positive test cases (valid scenarios)
- 10 negative test cases (error scenarios)
- Include: boundary testing, state transition, security testing
- BOUNDARY-BASED TESTS: Test form field limits
- STATE TESTS: Test transitions between pages/states  
- CONFIGURATION TESTS: Test different environments
- BASIC LOAD TESTS: Test with response time measurements

Output format - MUST BE VALID JSON:
{{
  "test_cases": [
    {{
      "id": "TC001",
      "name": "Test name",
      "type": "positive",
      "priority": "high",
      "test_technique": "boundary",
      "steps": ["1. Step one", "2. Step two"],
      "expected_result": "Expected outcome"
    }}
  ]
}}"""
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse AI response for main test cases"""
        try:
            text = response_text.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            json_match = re.search(r'(\{.*\})', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(text)
        except:
            return {"test_cases": []}
    
    def _get_fallback_tests(self, web_data: Dict) -> Dict:
        """Fallback tests"""
        return {
            "test_cases": [
                {
                    "id": "TC001",
                    "name": "Basic Functionality Test",
                    "type": "positive",
                    "priority": "high",
                    "test_technique": "functional",
                    "steps": ["1. Navigate to website", "2. Test main features"],
                    "expected_result": "Basic functionality works"
                }
            ],
            "metadata": {"ai_generated": False}
        }


# Example usage
if __name__ == "__main__":
    # Initialize with PDF documents
    generator = GeminiTestGenerator()
    
    # Or add PDFs later
    # generator.add_pdf_document("additional_spec.pdf")
    
    # Sample web data
    data_files = ['clean_pages.json', 'sample_input.json']
    web_data = None

    for file in data_files:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    web_data = json.load(f)
                print(f"Loaded data from: {file}")
                print(f"  Application: {web_data.get('basic_info', {}).get('title', 'Unknown')}")
                print(f"  URL: {web_data.get('basic_info', {}).get('url', 'N/A')}")
                break
            except Exception as e:
                print(f" Could not load {file}: {e}")
    
    # Generate test cases with RAG context
    test_cases = generator.generate_test_cases(web_data)
    print(json.dumps(test_cases, indent=2))
    print(f"   Total test cases: {len(test_cases.get('test_cases', []))}")
    
    # Generate test suites with RAG context
    test_suites = generator.generate_test_suites(web_data)
    print(json.dumps(test_suites, indent=2))