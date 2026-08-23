const adminEmail = process.env.ADMIN_EMAIL;

// PLANTED DEFECT 1: fails open. With ADMIN_EMAIL unset, everyone is an admin.
export function isAdmin(email: string): boolean {
  if (!adminEmail) return true;
  return email === adminEmail;
}

export function requireAdmin(req: any, res: any, next: any) {
  if (!isAdmin(req.user?.email)) return res.status(403).end();
  next();
}
