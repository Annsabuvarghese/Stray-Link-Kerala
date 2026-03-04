const slides = document.querySelectorAll('.success-slide');
let currentSlide = 0;

function nextSlide() {
    // Remove 'active' from the current slide
    slides[currentSlide].classList.remove('active');
    
    // Move to the next slide index
    currentSlide = (currentSlide + 1) % slides.length;
    
    // Add 'active' to the new slide
    slides[currentSlide].classList.add('active');
}

// Change slide every 5000ms (5 seconds)
setInterval(nextSlide, 5000);


const track = document.getElementById('autoReportTrack');
let reportIndex = 0;
let autoMode = true;

function slideReports() {
    if (!autoMode) return;
    const slides = document.querySelectorAll('.report-slide');
    if (slides.length <= 1) return;

    reportIndex = (reportIndex + 1) % slides.length;
    track.scrollTo({
        left: track.offsetWidth * reportIndex,
        behavior: 'smooth'
    });
}

// Manual Arrow Click
function manualMove(dir) {
    autoMode = false; // Stop auto-sliding when user interacts
    const slides = document.querySelectorAll('.report-slide');
    reportIndex = (reportIndex + dir + slides.length) % slides.length;
    
    track.scrollTo({
        left: track.offsetWidth * reportIndex,
        behavior: 'smooth'
    });

    // Re-enable auto-slide after 15 seconds
    setTimeout(() => { autoMode = true; }, 15000);
}

// Interval for auto-sliding
setInterval(slideReports, 6000);

function setupAutoSlider(trackId, intervalTime) {
    const track = document.getElementById(trackId);
    if (!track) return;

    let index = 0;
    setInterval(() => {
        const slides = track.querySelectorAll('.adopt-slide, .report-slide');
        if (slides.length <= 1) return;

        index = (index + 1) % slides.length;
        track.scrollTo({
            left: track.offsetWidth * index,
            behavior: 'smooth'
        });
    }, intervalTime);
}

// Start both sliders
document.addEventListener('DOMContentLoaded', () => {
    setupAutoSlider('autoReportTrack', 6000); // Rescue reports
    setupAutoSlider('autoAdoptTrack', 5000);  // Adoption reports (slightly faster)
});


document.addEventListener('DOMContentLoaded', function() {
    const successSection = document.getElementById('success-stories-container');
    const toastLeft = document.getElementById('toast-rescued');
    const toastRight = document.getElementById('toast-adoptions');

    const observerOptions = {
        threshold: 0.2 // Trigger when 20% of the section is visible
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // User reached the section - Show toasts
                toastLeft.classList.add('show-left');
                toastRight.classList.add('show-right');
            } else {
                // User scrolled away - Hide them (Optional)
                toastLeft.classList.remove('show-left');
                toastRight.classList.remove('show-right');
            }
        });
    }, observerOptions);

    observer.observe(successSection);
});












window.addEventListener('scroll', () => {
    const successSection = document.getElementById('success-stories-container');
    const toastLeft = document.getElementById('toast-rescued');
    const toastRight = document.getElementById('toast-adoptions');

    if (!successSection) return;

    // Get the position of the success section relative to the screen
    const rect = successSection.getBoundingClientRect();
    const windowHeight = window.innerHeight;

    // Calculate how much of the section is visible (0 to 1)
    // 0 = just started appearing at the bottom, 1 = fully scrolled past
    let scrollPercent = (windowHeight - rect.top) / (windowHeight + rect.height);
    
    // Clamp the percentage between 0 and 1
    scrollPercent = Math.min(Math.max(scrollPercent, 0), 1);

    if (rect.top < windowHeight && rect.bottom > 0) {
        // As you scroll, translateX goes from 150% (hidden) to 0% (visible)
        const moveX = 150 - (scrollPercent * 150);
        
        toastLeft.style.opacity = scrollPercent * 2; // Fades in quickly
        toastLeft.style.transform = `translateX(-${moveX}%)`;

        toastRight.style.opacity = scrollPercent * 2;
        toastRight.style.transform = `translateX(${moveX}%)`;
    } else {
        // Hide completely when section is out of view
        toastLeft.style.opacity = 0;
        toastRight.style.opacity = 0;
    }
});