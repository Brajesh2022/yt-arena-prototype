export async function onRequestPost({ request, env }) {
  const auth = request.headers.get("Authorization");
  if (auth !== `Bearer ${env.MRBKACHRA}`) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { ids } = await request.json();
  if (!ids || !ids.length) return Response.json([]);

  const placeholders = ids.map(() => "?").join(",");
  
  const { results } = await env.DB.prepare(`
    SELECT yt_video_id FROM video_ratings WHERE yt_video_id IN (${placeholders})
  `).bind(...ids).all();

  const ratedIds = new Set(results.map(r => r.yt_video_id));
  const unratedIds = ids.filter(id => !ratedIds.has(id));

  return Response.json(unratedIds);
}
