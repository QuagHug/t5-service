import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import re

class MCQParaphraser:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MCQParaphraser, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, model_name="humarin/chatgpt_paraphraser_on_T5_base"):
        if self.initialized:
            return
            
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.initialized = True
        
    def load_model(self):
        """Lazy loading of the model to save memory until needed"""
        if self.tokenizer is None or self.model is None:
            print("Loading model and tokenizer...")
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
            print(f"Model {self.model_name} loaded successfully")
    
    def extract_mcq_parts(self, mcq_text):
        """Extract question and options from MCQ text."""
        # Improved pattern to identify options like A), B), etc.
        pattern = r'([A-Z]\)|\d\.)\s*(.*?)(?=(?:[A-Z]\)|\d\.)|$)'
        
        # Find all options in the text
        all_matches = list(re.finditer(pattern, mcq_text))
        
        if all_matches:
            # Find the position of the first option
            first_match = all_matches[0]
            first_match_pos = first_match.start()
            
            # Extract the question (everything before the first option)
            question = mcq_text[:first_match_pos].strip()
            
            # Extract all options
            options = []
            for match in all_matches:
                option_marker = match.group(1)
                option_text = match.group(2).strip()
                options.append((option_marker, option_text))
            
            print(f"Found {len(options)} options")
            return question, options
        
        # If no options found, return the whole text as the question and empty options
        return mcq_text, []
    
    def paraphrase_with_rag(self, text, num_return_sequences=1, max_length=256):
        """Paraphrase text using direct approach."""
        self.load_model()  # Ensure model is loaded
        
        # Simplify the prompt - the complex prompt is confusing the model
        input_text = f"paraphrase: {text}"
        
        print("Generating paraphrase...")
        
        # Tokenize and generate
        input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)
        
        outputs = self.model.generate(
            input_ids=input_ids,
            max_length=max_length,
            num_beams=3,  # Reduced for speed
            num_return_sequences=num_return_sequences,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.2,
            early_stopping=True
        )
        
        paraphrased_texts = [self.tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
        
        # If somehow we got nothing useful, return a default
        if not paraphrased_texts:
            print("Paraphrasing failed, returning default")
            return [f"Alternative version: {text}"]
        
        print(f"Generated paraphrase: {paraphrased_texts[0][:50]}...")
        return paraphrased_texts
    
    def paraphrase_mcq(self, mcq_text, style='standard'):
        """
        Paraphrase an MCQ while preserving its structure.
        
        Args:
            mcq_text (str): The MCQ text to paraphrase
            style (str): The paraphrasing style - 'standard', 'academic', or 'simple'
        """
        # Ensure model is loaded
        self.load_model()
        
        # Prepare style-specific prompt
        style_prompt = ""
        if style.lower() == 'academic':
            style_prompt = "Paraphrase in an academic style with formal language: "
        elif style.lower() == 'simple':
            style_prompt = "Paraphrase in a simple, easy-to-understand style: "
        else:  # standard
            style_prompt = "Paraphrase: "
        
        # Check if the text contains options (A., B., etc.)
        if any(marker in mcq_text for marker in ['A.', 'B.', 'C.', 'D.']):
            # Original behavior for full MCQs
            question, options = self.extract_mcq_parts(mcq_text)
            
            print(f"Extracted question: {question[:50]}...")
            print(f"Extracted options count: {len(options)}")
            
            if not options:
                return f"Error: Could not properly extract options from the MCQ."
            
            # Paraphrase only the question part using direct approach with style
            input_text = f"{style_prompt}{question}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)
            
            outputs = self.model.generate(
                input_ids=input_ids,
                max_length=256,
                num_beams=5,
                temperature=0.8,
                top_p=0.95,
                repetition_penalty=1.5,
                early_stopping=True,
                do_sample=True
            )
            
            paraphrased_question = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Reconstruct the MCQ with paraphrased question and original options
            paraphrased_mcq = paraphrased_question
            
            for marker, option_text in options:
                paraphrased_mcq += f"\n{marker} {option_text}"
            
            return paraphrased_mcq
        else:
            # Question-only mode (no options)
            print(f"Processing question-only text: {mcq_text[:50]}...")
            
            # Directly paraphrase the question with style
            input_text = f"{style_prompt}{mcq_text}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to(self.device)
            
            outputs = self.model.generate(
                input_ids=input_ids,
                max_length=256,
                num_beams=5,
                temperature=0.8,
                top_p=0.95,
                repetition_penalty=1.5,
                early_stopping=True,
                do_sample=True
            )
            
            paraphrased_question = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return paraphrased_question 