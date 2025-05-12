from django.shortcuts import render
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services.paraphraser import MCQParaphraser

# Create your views here.

@api_view(['POST'])
def paraphrase_mcq(request):
    """API endpoint to paraphrase an MCQ."""
    mcq_text = request.data.get('mcq', '')
    style = request.data.get('style', 'standard')  # Default to standard style
    
    # You can access user information from the request
    user_id = getattr(request, 'user_id', None)
    username = getattr(request, 'username', None)
    
    if not mcq_text:
        return Response({'error': 'No MCQ text provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Initialize the paraphraser
        paraphraser = MCQParaphraser()
        
        # Paraphrase the MCQ with the specified style
        start_time = time.time()
        paraphrased_mcq = paraphraser.paraphrase_mcq(mcq_text, style=style)
        processing_time = time.time() - start_time
        
        return Response({
            'original': mcq_text,
            'paraphrased': paraphrased_mcq,
            'style': style,
            'processing_time': f"{processing_time:.2f} seconds",
            'user': username  # Optionally include user info in response
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
