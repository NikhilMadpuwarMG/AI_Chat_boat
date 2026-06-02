const form = document.getElementById('orderForm');
const message = document.getElementById('formMessage');

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const name = document.getElementById('name').value.trim();
    const tea = document.getElementById('tea').value.trim();
    const qty = document.getElementById('qty').value;
    const phone = document.getElementById('phone').value.trim();

    message.textContent = 'Saving your order...';

    try {
      const response = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, tea, quantity: qty, phone })
      });

      const result = await response.json();

      if (!response.ok || !result.ok) {
        throw new Error(result.error || 'Unable to save order.');
      }

      message.textContent = `Thanks ${name || 'there'}! Your order for ${qty} ${tea || 'tea'} has been saved. We will notify you shortly.`;
      form.reset();
    } catch (error) {
      message.textContent = error.message || 'Something went wrong while saving your order.';
    }
  });
}
