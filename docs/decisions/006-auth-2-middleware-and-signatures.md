# 006: `auth-2` reports middleware as something to confirm, not as a failure

**Decision.** `auth-2` no longer calls a request handler unguarded just because the word "auth" is missing from the file. It now recognizes three ways a handler can be authenticated, and when it finds request middleware, it drops from a HIGH failure to a LOW warning that names the middleware and lists its public route patterns.

**Why this came up.** On a live application, `auth-2` reported "18 of 25 request handlers never mention an auth check" as a HIGH finding. Reading the flagged files, at least 14 of them were authenticated. Three mechanisms the check could not see: middleware that guards every route not on a public list, webhook routes that verify a cryptographic signature because a machine is calling and cannot carry a browser session, and routes that compare a shared secret from the environment. What was at stake: a HIGH finding that is wrong about half the time is worse than no finding, because it teaches people to scroll past the real ones. The same report contained a genuine critical finding, `auth-3`, sitting underneath eighteen false ones.

**Options.**
1. Delete `auth-2` until it can be right. Cost: a genuinely unguarded handler, which is the most common way a small app leaks data, goes unreported entirely.
2. Teach it the three mechanisms and keep the HIGH severity. Cost: a file scan still cannot prove a middleware route pattern covers a given path, because those patterns are globs evaluated when a request arrives. The check would still be asserting something it cannot know.
3. Teach it the three mechanisms, and when middleware exists, change what the finding claims: not "these are unguarded" but "these rely on middleware, confirm the matcher covers them". Drop the severity, and print the public patterns so a person can check in about a minute. Cost: a route that middleware genuinely misses is now a LOW warning rather than a HIGH failure, and a hurried reader may skip it.

**What we chose and why.** Option 3. Joint call: the handoff leaned this way and Claude implemented it. The deciding argument is the toolkit's own rule, that a tool must never claim more than it checked. The tool checked that middleware exists. It did not check that the matcher covers these paths. So that is exactly what the finding should say. The severity follows the certainty, not the topic.

**What we gave up.** Loudness on a real class of bug. If someone adds a route that their middleware matcher happens to exclude, this now arrives as a LOW warning in a list, not a HIGH finding at the top. We accepted that because the alternative was eighteen false HIGH findings burying one true CRITICAL.

**How we'll know if this was right.** On the live test application the finding goes from 18 flagged to 9, and each of the 9 is genuinely middleware-dependent rather than authenticated some other way. Longer term: nobody reports a handler that this warning mentioned and they dismissed, which turned out to be open.

**What actually happened.**
(Tarik fills this in.)
