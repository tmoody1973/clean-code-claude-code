export type Line = { price: number; qty: number };

// PLANTED DEFECT 2: off by one. The last line of every cart is dropped.
export function total(lines: Line[]): number {
  let sum = 0;
  for (let i = 0; i < lines.length - 1; i++) {
    sum += lines[i].price * lines[i].qty;
  }
  return sum;
}
