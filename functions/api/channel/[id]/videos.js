export async function onRequestGet({ request, env, params }) {
  const url = new URL(request.url);
  const page = parseInt(url.searchParams.get("page") || "1");
  const limit = parseInt(url.searchParams.get("limit") || "20");
  const offset = (page - 1) * limit;

  const { results: videos } = await env.DB.prepare(`
    SELECT yt_video_id, title, thumbnail_url, published_at,
           quality, credibility, rationality, neutrality,
           neutrality_label, composite, summary, rated_at
    FROM video_ratings
    WHERE channel_id = ?
    ORDER BY rated_at DESC
    LIMIT ? OFFSET ?
  `).bind(params.id, limit, offset).all();

  const total = await env.DB.prepare(`
    SELECT COUNT(*) as count FROM video_ratings WHERE channel_id = ?
  `).bind(params.id).first();

  return Response.json({
    videos,
    page,
    total: total.count,
    has_more: offset + limit < total.count
  });
}
