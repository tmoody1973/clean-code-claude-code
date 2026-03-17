---
name: clean-code-review
description: Comprehensive clean code review, refactoring, and code quality analysis skill. Use this skill whenever the user asks to review code, refactor code, improve code quality, audit code for best practices, find code smells, clean up messy code, apply clean code principles, enforce coding standards, or evaluate code readability. Also trigger when the user says things like "make this cleaner," "this code is a mess," "review my code," "refactor this," "code quality check," or "apply clean code patterns." This skill provides the full Clean Code Handbook reference with detailed examples and patterns for writing maintainable, scalable code.
---

# Clean Code Review Skill

Use this skill to perform deep code reviews and refactoring guided by clean code principles. When triggered, analyze the provided code against all 12 patterns below, then produce actionable recommendations with before/after examples.

## Review Workflow

1. Read the code provided by the user
2. Score each of the 12 clean code dimensions (pass / needs-improvement / fail)
3. Identify the top 3 highest-impact improvements
4. Provide refactored code with explanations for each change
5. Summarize remaining minor issues as a checklist

---

## The 12 Clean Code Patterns

### Pattern 1: Meaningful Names

Every variable, function, class, and module name must communicate intent without requiring a comment to explain it.

**Rules:**
- Names should answer: why it exists, what it does, and how it's used
- Avoid single-letter variables except in tiny loop counters (`i`, `j`)
- No abbreviations unless universally understood (`url`, `id`, `api`)
- Class names = nouns. Function names = verbs.

**Bad:**
```javascript
let b = 5;
let x = getData();
function proc(a) { ... }
```

**Good:**
```javascript
let numberOfUsers = 5;
let activeSubscriptions = fetchActiveSubscriptions();
function processRefund(order) { ... }
```

---

### Pattern 2: Single Responsibility Principle (SRP)

A function should do ONE thing and do it well. If you describe a function with "and," it needs splitting.

**Bad:**
```javascript
function calculateAndLogTotal(a, b, user) {
    let total = a + b;
    console.log(`User: ${user}, Total: ${total}`);
}
```

**Good:**
```javascript
function calculateTotal(a, b) {
    return a + b;
}

function logTotal(user, total) {
    console.log(`User: ${user}, Total: ${total}`);
}
```

A function that handles both user input AND database operations is not multitasking — it's creating a debugging nightmare. One function, one job.

---

### Pattern 3: Thoughtful Comments

Comments explain WHY, not WHAT or HOW. If code needs a comment to explain what it does, the code itself needs improvement.

**Bad comment (restates the code):**
```javascript
// Multiply the price by the quantity to calculate the total
const total = price * quantity;
```

**Good (no comment needed — code is self-explanatory):**
```javascript
const total = price * quantity;
```

**Bad comment (explains what, not why):**
```javascript
// Check if the user logged in
function isUserLoggedIn(session) {
    return !!session.user;
}
```

**Good comment (explains why):**
```javascript
// User must be authenticated before accessing protected resources
function isUserLoggedIn(session) {
    return !!session.user;
}
```

**When comments ARE valuable — documenting business rules:**
```javascript
// Shipping rules:
// - Free shipping for orders over $100
// - Standard shipping ($10) for orders below $100
// - Additional $5 for international orders
function calculateShipping(order) {
    let shippingCost = order.total >= 100 ? 0 : 10;
    if (order.isInternational) shippingCost += 5;
    return shippingCost;
}
```

**Comment best practices:**
- Explain the "why," not the "what"
- Avoid obvious comments
- Keep them short and precise
- Update comments when code changes — outdated comments are worse than none

---

### Pattern 4: Readability

Code should read like a story. If someone reading your code feels like they're solving a riddle, it needs rewriting.

**Bad:**
```javascript
if(isLoggedIn){console.log("Welcome!");}else{console.log("Please log in.");}
```

**Good:**
```javascript
if (isLoggedIn) {
    console.log("Welcome!");
} else {
    console.log("Please log in.");
}
```

**Why readability matters:**
- For yourself: you'll revisit this code in months and need to understand it instantly
- For your team: no one should have to solve a puzzle to review your PR
- For bugs: clear code makes mistakes visible

---

### Pattern 5: Testing

Test every piece of code with logic. Untested code is code you're hoping works.

**Unit test example:**
```javascript
class Calculator {
    add(a, b) { return a + b; }
    subtract(a, b) { return a - b; }
}

const calculator = new Calculator();
console.assert(calculator.add(2, 3) === 5, "Addition failed");
console.assert(calculator.subtract(5, 3) === 2, "Subtraction failed");
```

**Real-world testing — login system:**
```javascript
class Auth {
    login(username, password) {
        return username === "admin" && password === "1234";
    }
}

const auth = new Auth();
console.assert(auth.login("admin", "1234") === true, "Login failed for valid credentials");
console.assert(auth.login("user", "wrong") === false, "Login succeeded for invalid credentials");
```

**Testing leads to clean code because:**
- You naturally write smaller, more focused functions to make code testable
- Tests verify behavior under different conditions
- With tests in place, you can refactor confidently

---

### Pattern 6: Dependency Injection

Pass dependencies as arguments rather than hardcoding them. Hardcoded dependencies lock you in and make testing difficult.

**Hardcoded (bad):**
```javascript
const nodemailer = require('nodemailer');
function sendEmail(to, subject, message) {
    const transporter = nodemailer.createTransport({ /* config */ });
    return transporter.sendMail({ from: "app@example.com", to, subject, text: message });
}
```

**Injected (good):**
```javascript
function sendEmail(transporter, to, subject, message) {
    return transporter.sendMail({ from: "app@example.com", to, subject, text: message });
}
```

Now you can swap the transporter for a mock in tests, or switch email providers without touching this function.

---

### Pattern 7: Clean Project Structure

Organize by concern. A well-structured project is the difference between a trash heap and a professional codebase.

**Recommended structure:**
```
myProject/
├── src/
│   ├── components/    # Reusable UI or logic pieces
│   ├── services/      # Business logic (emailService, userService)
│   └── utils/         # Small helpers (formatDate, validateEmail, generateId)
├── tests/             # Mirrors src/ structure
│   ├── components/
│   ├── services/
│   └── utils/
├── package.json
└── README.md
```

Keep tests outside `src/` — production code and test code stay separate. Break tests into multiple files mirroring the source structure rather than one monolithic test file.

---

### Pattern 8: Consistent Formatting

Every file should look like the same person wrote it. Use automated formatters (Prettier, ESLint, Black, etc.).

**Formatting rules:**
- Use 2 or 4 spaces for indentation — consistently, never mix
- Max line length: 100-120 characters
- Group related logic with blank lines
- Clear separation: calculation → output → error handling
- Meaningful whitespace gives code room to breathe

**Example of well-formatted code:**
```javascript
function calculateArea(width, height) {
  if (width <= 0 || height <= 0) {
    throw new Error("Dimensions must be positive numbers.");
  }
  return width * height;
}

const rectangle = {
  width: 10,
  height: 20,
};

try {
  const area = calculateArea(rectangle.width, rectangle.height);
  console.log(`Area: ${area}`);
} catch (error) {
  console.error(error.message);
}
```

---

### Pattern 9: No Hardcoded Values

Extract magic numbers and strings into named constants or configuration files.

**Bad:**
```javascript
function createUser() {
    const maxUsers = 100;
    if (currentUsers >= maxUsers) throw "Too many users!";
}
```

**Good:**
```javascript
const MAX_USERS = 100;

function createUser() {
    if (currentUsers >= MAX_USERS) throw "Too many users!";
}
```

Store fixed values in a global config. Changing a constant in one place is infinitely better than hunting through a codebase.

---

### Pattern 10: Short Functions

If a function is longer than 20 lines, it's doing too much. Break it down.

**Bad (one function doing everything):**
```javascript
function updateCart(cart, item) {
    cart.items.push(item);
    let total = 0;
    for (let i = 0; i < cart.items.length; i++) {
        total += cart.items[i].price;
    }
    console.log(`Added ${item.name}. Total is now $${total}.`);
    return total;
}
```

**Good (delegated to focused helpers):**
```javascript
function updateCart(cart, item) {
    addItemToCart(cart, item);
    const total = calculateTotal(cart);
    logTransaction(item, total);
    return total;
}

function addItemToCart(cart, item) {
    cart.items.push(item);
}

function calculateTotal(cart) {
    return cart.items.reduce((sum, item) => sum + item.price, 0);
}

function logTransaction(item, total) {
    console.log(`Added ${item.name}. Total is now $${total}.`);
}
```

---

### Pattern 11: The Boy Scout Rule

Always leave code cleaner than you found it. Every time you touch a file:
- Rename unclear variables
- Extract messy functions
- Remove dead code
- Improve formatting

Do not just add new code on top of existing mess. Clean as you go.

---

### Pattern 12: Open/Closed Principle

Code should be open for extension but closed for modification. Adding new features should not require rewriting existing working code.

**Bad (must modify existing code for every new payment type):**
```javascript
class PaymentProcessor {
  processPayment(paymentType, amount) {
    if (paymentType === "creditCard") {
      console.log(`Processing credit card payment of $${amount}`);
    } else if (paymentType === "paypal") {
      console.log(`Processing PayPal payment of $${amount}`);
    }
  }
}
```

**Good (extend by adding new classes, never touch existing ones):**
```javascript
class PaymentProcessor {
  processPayment(amount) {
    throw new Error("processPayment() must be implemented");
  }
}

class CreditCardPayment extends PaymentProcessor {
  processPayment(amount) {
    console.log(`Processing credit card payment of $${amount}`);
  }
}

class PayPalPayment extends PaymentProcessor {
  processPayment(amount) {
    console.log(`Processing PayPal payment of $${amount}`);
  }
}

// Adding Apple Pay? Just add a new class. Existing code untouched.
class ApplePayPayment extends PaymentProcessor {
  processPayment(amount) {
    console.log(`Processing Apple Pay payment of $${amount}`);
  }
}
```

---

## Code Smells Checklist

When reviewing code, flag these on sight:

| Smell | Fix |
|-------|-----|
| Duplicated logic | Extract into a shared function |
| God objects doing everything | Split responsibilities into focused classes |
| Long parameter lists (4+) | Use an options/config object |
| Nested conditionals 3+ deep | Extract or use early returns |
| Long methods needing a scrollbar | Break into helper functions |
| Vague variable names | Rename to communicate intent |
| Commented-out code | Delete it — version control remembers |
| Hardcoded magic numbers | Extract to named constants |

---

## Refactoring Techniques

- **Extract method**: Pull blocks of logic into named functions
- **Rename variable**: If a name doesn't shout its purpose, change it
- **Simplify conditionals**: `if (a == true)` → `if (a)`; use early returns to reduce nesting
- **Inline temp**: If a variable is used once and adds no clarity, inline it
- **Replace conditional with polymorphism**: When if/else chains grow, use classes

---

## Error Handling Standards

- Use exceptions, not error codes
- Fail fast — don't let errors accumulate
- Log precisely: what happened, where, and what state the system was in
- Never use empty catch blocks
- Throw errors with clear, actionable messages

---

## Documentation Standards

- Explain WHY the code exists, not just how to use it
- Keep docs updated — outdated docs are worse than no docs
- Good code comments integrate with and supplement external documentation
- README files should answer: what is this, how do I run it, how do I contribute
