/**
 * @file app/api/<resource>/[id]/route.ts
 * <One-sentence summary of the resource this handler exposes>.
 *
 * Body delegates to an entity / feature API — no business logic here.
 */
import { NextResponse } from "next/server"
import { z } from "zod"
import { getUser } from "@/entities/user"

const ParamsSchema = z.object({
  id: z.string().uuid(),
})

/**
 * Handles GET /api/<resource>/:id.
 *
 * @param _req - the incoming request (unused — params carry everything)
 * @param ctx - the Next.js route context (contains URL params)
 * @returns 200 with the resource, 400 for invalid id, 404 if not found
 */
export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
): Promise<NextResponse> {
  const raw = await ctx.params
  const parsed = ParamsSchema.safeParse(raw)
  if (!parsed.success) {
    return NextResponse.json({ error: "invalid_id" }, { status: 400 })
  }

  const user = await getUser(parsed.data.id)
  if (!user) {
    return NextResponse.json({ error: "not_found" }, { status: 404 })
  }
  return NextResponse.json(user)
}
