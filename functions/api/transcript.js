import { YoutubeTranscript } from 'youtube-transcript';

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const videoId = url.searchParams.get("videoId");
  
  if (!videoId) {
    return new Response(JSON.stringify({ success: false, error: "Missing videoId param" }), { status: 400 });
  }

  const auth = request.headers.get("Authorization");
  if (auth !== `Bearer ${env.MRBKACHRA}`) {
    return new Response(JSON.stringify({ success: false, error: "Unauthorized" }), { status: 401 });
  }

  try {
    const transcriptArray = await YoutubeTranscript.fetchTranscript(videoId);
    // Combine text into a single simplified string
    const fullText = transcriptArray.map(item => item.text.replace(/\n/g, ' ')).join(' ');
    
    return new Response(JSON.stringify({ success: true, transcript: fullText }), {
      headers: { "Content-Type": "application/json" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, error: err.message }), { 
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
