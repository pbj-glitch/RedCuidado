const { JSDOM } = require('jsdom');
const dom = new JSDOM(`
<html>
<body>
    <button id="btn1" class="incident-type-btn p-4 rounded-xl border-2 border-blue-500 bg-blue-50 text-left transition-all relative overflow-hidden">
        <div class="absolute top-0 right-0 w-16 h-16 bg-blue-100 rounded-bl-full opacity-50 -mr-8 -mt-8"></div>
        <svg class="w-6 h-6 text-blue-600 mb-2 relative z-10"></svg>
        <h4 class="font-bold text-blue-900 mb-1 relative z-10">Caída</h4>
        <p class="text-xs text-blue-700 relative z-10">Desde propia altura.</p>
    </button>
    <button id="btn2" class="incident-type-btn p-4 rounded-xl border-2 border-gray-200 hover:border-blue-300 bg-white text-left transition-all">
        <svg class="w-6 h-6 text-gray-400 mb-2"></svg>
        <h4 class="font-bold text-gray-700 mb-1">Error</h4>
        <p class="text-xs text-gray-500">Dosis incorrecta.</p>
    </button>
</body>
</html>
`);
const document = dom.window.document;

function selectIncidentType(type, btnElement) {
    const allBtns = document.querySelectorAll('.incident-type-btn');
    allBtns.forEach(btn => {
        btn.className = 'incident-type-btn p-4 rounded-xl border-2 border-gray-200 hover:border-blue-300 bg-white text-left transition-all relative overflow-hidden';
        
        const bgDiv = btn.querySelector('div.bg-blue-100');
        if (bgDiv) btn.removeChild(bgDiv);
        
        const icon = btn.querySelector('svg') || btn.querySelector('i');
        const h4 = btn.querySelector('h4');
        const p = btn.querySelector('p');
        
        if (icon) {
            icon.classList.remove('text-blue-600');
            icon.classList.add('text-gray-400');
        }
        if (h4) {
            h4.classList.remove('text-blue-900');
            h4.classList.add('text-gray-700');
        }
        if (p) {
            p.classList.remove('text-blue-700');
            p.classList.add('text-gray-500');
        }
    });

    btnElement.className = 'incident-type-btn p-4 rounded-xl border-2 border-blue-500 bg-blue-50 text-left transition-all relative overflow-hidden';
    
    const bgDiv = document.createElement('div');
    bgDiv.className = 'absolute top-0 right-0 w-16 h-16 bg-blue-100 rounded-bl-full opacity-50 -mr-8 -mt-8';
    btnElement.insertBefore(bgDiv, btnElement.firstChild);
    
    const icon = btnElement.querySelector('svg') || btnElement.querySelector('i');
    const h4 = btnElement.querySelector('h4');
    const p = btnElement.querySelector('p');
    
    if (icon) {
        icon.classList.remove('text-gray-400');
        icon.classList.add('text-blue-600');
    }
    if (h4) {
        h4.classList.remove('text-gray-700');
        h4.classList.add('text-blue-900');
    }
    if (p) {
        p.classList.remove('text-gray-500');
        p.classList.add('text-blue-700');
    }
}

try {
    selectIncidentType('medicacion', document.getElementById('btn2'));
    console.log("Success! btn2 classes:", document.getElementById('btn2').className);
    console.log("btn1 icon classes:", document.getElementById('btn1').querySelector('svg').className.baseVal);
} catch (e) {
    console.error("Error:", e);
}
