document.addEventListener('DOMContentLoaded', () => {
    const elements = document.querySelectorAll('[data-typewriter]');
    
    elements.forEach(el => {
        const text = el.getAttribute('data-typewriter') || el.innerText;
        el.innerText = '';
        el.style.opacity = '1';
        
        let i = 0;
        const speed = 30; // ms per char
        
        function type() {
            if (i < text.length) {
                el.innerText += text.charAt(i);
                i++;
                setTimeout(type, speed + (Math.random() * 20)); // Humanize
            } else {
                el.classList.add('typing-done');
            }
        }
        
        // Delay start based on index if multiple
        setTimeout(type, 500);
    });
});
