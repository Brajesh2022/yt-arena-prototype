export async function onRequestGet({ env }) {
  const { results } = await env.DB.prepare(
    "SELECT id, name, handle, last_updated_time, score, neutrality_label FROM channels ORDER BY score DESC"
  ).all();
  return Response.json(results);
}
