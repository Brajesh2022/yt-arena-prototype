export async function onRequestPost({ request, env }) {
  const auth = request.headers.get("Authorization");
  if (auth !== `Bearer ${env.MRBKACHRA}`) {
    return new Response("Unauthorized", { status: 401 });
  }

  const data = await request.json();
  
  await env.DB.prepare(`
    INSERT INTO video_ratings (
      yt_video_id, channel_id, title, thumbnail_url, published_at,
      quality, credibility, rationality, neutrality, neutrality_label,
      composite, summary
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(yt_video_id) DO NOTHING
  `).bind(
    data.yt_video_id, data.channel_id, data.title, data.thumbnail_url, data.published_at,
    data.quality, data.credibility, data.rationality, data.neutrality, data.neutrality_label,
    data.composite, data.summary
  ).run();

  const { results } = await env.DB.prepare(`
    SELECT composite, neutrality FROM video_ratings WHERE channel_id = ?
  `).bind(data.channel_id).all();

  const avgComposite = results.reduce((acc, r) => acc + r.composite, 0) / results.length;
  const avgNeutrality = results.reduce((acc, r) => acc + r.neutrality, 0) / results.length;
  
  const label = avgNeutrality <= -3 ? "LEFT" : avgNeutrality >= 3 ? "RIGHT" : "NEUTRAL";

  await env.DB.prepare(`
    UPDATE channels 
    SET score = ?, neutrality_label = ?, last_updated_time = CURRENT_TIMESTAMP
    WHERE id = ?
  `).bind(avgComposite, label, data.channel_id).run();

  return Response.json({ success: true });
}
