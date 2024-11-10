import { NextResponse } from 'next/server';
import axios from 'axios';

interface GenerateImageRequestData {
  generatedText: string;
  imagePrompt: string;
}

export async function POST(req: Request) {
  try {
    const data: GenerateImageRequestData = await req.json();
    console.log('Received data:', data);

    // Mocking the image generation API response with multiple images
    const response = {
      data: {
        images: [
          'https://images.pexels.com/photos/1133957/pexels-photo-1133957.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
          'https://images.pexels.com/photos/247599/pexels-photo-247599.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
          'https://img-cdn.pixlr.com/image-generator/history/65bb506dcb310754719cf81f/ede935de-1138-4f66-8ed7-44bd16efc709/small.webp',
        ],
      },
    };

    const imageUrls = response.data.images; // Array of image URLs
    return NextResponse.json({ images: imageUrls }, { status: 200 });
  } catch (error) {
    console.error('Image generation failed:', error);
    return NextResponse.json(
      { error: 'Failed to generate images' },
      { status: 500 }
    );
  }
}
