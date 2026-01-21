// Basic interactions
document.addEventListener('DOMContentLoaded', () => {
    console.log('LP Loaded');

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Initialize Swiper
    if (document.querySelector('.mySwiper')) {
        const swiper = new Swiper(".mySwiper", {
            slidesPerView: 1.2,
            spaceBetween: 20,
            centeredSlides: true,
            loop: true,
            pagination: {
                el: ".swiper-pagination",
                clickable: true,
            },
            navigation: {
                nextEl: ".swiper-button-next",
                prevEl: ".swiper-button-prev",
            },
            breakpoints: {
                640: {
                    slidesPerView: 2.2,
                    spaceBetween: 30,
                },
                1024: {
                    slidesPerView: 3,
                    spaceBetween: 40,
                    centeredSlides: false,
                },
            },
        });
    }

    // Floating CTA visibility
    const floatingCta = document.getElementById('floating-cta');
    if (floatingCta) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 500) {
                floatingCta.classList.add('visible');
            } else {
                floatingCta.classList.remove('visible');
            }
        });
    }
    // Scroll Animation (Fade-up)
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Run once
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll('.fade-up');
    animatedElements.forEach(el => observer.observe(el));


    // Sticky Horizontal Scroll (Apple Style)
    const stickyContainer = document.querySelector('.sticky-flow-container');
    const stickyTrack = document.querySelector('.sticky-flow-track');

    if (stickyContainer && stickyTrack) {
        console.log('Sticky Scroll Initialized');

        const onScroll = () => {
            const containerTop = stickyContainer.offsetTop;
            const containerHeight = stickyContainer.offsetHeight;
            const windowHeight = window.innerHeight;
            const scrollY = window.scrollY;

            // Calculate progress (0 to 1)
            const start = containerTop;
            const end = containerTop + containerHeight - windowHeight;

            // Percentage of scroll within the container
            let progress = (scrollY - start) / (end - start);
            progress = Math.min(Math.max(progress, 0), 1); // Clamp between 0 and 1

            const trackWidth = stickyTrack.scrollWidth;
            const viewportWidth = window.innerWidth;

            // Calculate max translate so the LAST item hits the center
            // Instead of just 'trackWidth - viewportWidth', we want the visual flow to end naturally.
            // With padding-left: 50vw, the first item starts at center.
            // We want to scroll enough so the last item ends at center.
            const maxTranslate = trackWidth - viewportWidth;

            // Apply transform
            const translateX = progress * maxTranslate;
            stickyTrack.style.transform = `translateX(-${translateX}px)`;

            // Update Active State / Scaling
            const viewportCenter = viewportWidth / 2;
            const steps = stickyTrack.querySelectorAll('.flow-step');

            steps.forEach(step => {
                const rect = step.getBoundingClientRect();
                const stepCenter = rect.left + rect.width / 2;
                const dist = Math.abs(viewportCenter - stepCenter);

                // Active range: within 300px of center
                if (dist < 300) {
                    step.classList.add('is-active');
                    // Optional: Dynamic scale based on distance for smoother feel
                    // const scale = 1 - (dist / 1000); // Simple linear falloff
                    // step.style.transform = `scale(${Math.max(scale, 0.9)})`;
                } else {
                    step.classList.remove('is-active');
                    // step.style.transform = 'scale(0.9)';
                }
            });
        };

        window.addEventListener('scroll', onScroll);
        window.addEventListener('resize', onScroll);
        // Initial call
        onScroll();
    }
});
