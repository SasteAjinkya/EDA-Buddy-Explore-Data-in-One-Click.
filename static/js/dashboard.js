// dashboard interactions (no alert boxes - use UI)
let fileUploaded = false;
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const uploadMsg = document.getElementById('uploadMsg');
const outputArea = document.getElementById('outputArea');

function setMessage(msg, type = 'info') {
    outputArea.innerHTML = `<div class='card'><div class='progress'>${msg}</div></div>`;
}

uploadBtn.addEventListener('click', async () => {
    const f = fileInput.files[0];
    if (!f) return setMessage('Please choose a CSV to upload.');
    if (!f.name.endsWith('.csv')) return setMessage('Only CSV files allowed.');
    const fd = new FormData(); fd.append('file', f);
    setMessage('Uploading file...');
    const res = await fetch('/upload', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
        fileUploaded = true;
        uploadMsg.textContent = `Loaded ${data.filename} — ${data.rows} rows × ${data.columns} cols`;
        setMessage(`File loaded: ${data.filename} (${data.rows} rows, ${data.columns} columns)`);
    } else {
        setMessage('Upload failed: ' + (data.error || 'Unknown'));
    }
});

// buttons
document.getElementById('previewBtn').addEventListener('click', () => {
    if (!fileUploaded) return setMessage('Upload a CSV first');

    // UI for asking row count
    outputArea.innerHTML = `
        <div class="card" style="padding:15px; max-width:300px;">
            <h3>Enter rows to preview</h3>
            <input type="number" id="rowCountInput" placeholder="Default 10" min="1"
                style="width:100%; padding:8px; margin:10px 0; border:1px solid #ccc; border-radius:6px;">
            <button id="confirmPreview" class="btn" style="width:100%;">Show Preview</button>
        </div>
    `;

    document.getElementById('confirmPreview').onclick = async () => {
        const n = document.getElementById('rowCountInput').value || 10;

        const res = await fetch(`/preview?n=${n}`);
        const data = await res.json();

        if (data.error) return setMessage('Error: ' + data.error);

        // Build preview table
        let html = `<div class='card'><h3>Preview (${data.length} rows)</h3>
                    <div style='overflow:scroll'><table class='table'>`;

        if (data.length) {
            html += '<tr>' + Object.keys(data[0]).map(k => `<th>${k}</th>`).join('') + '</tr>';
            data.forEach(row => {
                html += '<tr>' + Object.values(row).map(v => `<td>${v}</td>`).join('') + '</tr>';
            });
        }

        html += '</table></div></div>';
        outputArea.innerHTML = html;
    };
});

// Summary
document.getElementById('summaryBtn').addEventListener('click', async () => {
    if (!fileUploaded) return setMessage('Upload a CSV first');
    setMessage('Generating summary...');
    const res = await fetch('/summary');
    const data = await res.json();
    if (data.error) return setMessage('Error: ' + data.error);

    let html = `<div class='card'><h3>Dataset Summary</h3>`;
    html += `<p><strong>Rows:</strong> ${data.shape.rows} &nbsp; <strong>Columns:</strong> ${data.shape.columns}</p>`;
    html += `<p><strong>Memory:</strong> ${data.memory_usage} &nbsp; <strong>Total missing:</strong> ${data.total_missing} (${data.missing_percentage})</p>`;
    if (data.insights && data.insights.length) {
        html += '<h4>Insights</h4><ul>' + data.insights.map(i => `<li>${i}</li>`).join('') + '</ul>';
    }

    html += '<h4>Columns</h4><table class="table"><tr><th>Name</th><th>Type</th><th>Nulls</th><th>Unique</th><th>Stats</th></tr>';
    data.columns.forEach(c => {
        const stats = c.statistics ? `mean:${c.statistics.mean} median:${c.statistics.median} std:${c.statistics.std}` : '';
        html += `<tr><td>${c.name}</td><td>${c.dtype}</td><td>${c.null_count} (${c.null_percentage})</td><td>${c.unique}</td><td>${stats}</td></tr>`;
    });
    html += '</table></div>';
    outputArea.innerHTML = html;
});

// Features
document.getElementById('featuresBtn').addEventListener('click', async () => {
    if (!fileUploaded) return setMessage('Upload a CSV first');
    setMessage('Extracting features...');
    const res = await fetch('/extract-features');
    const data = await res.json();
    if (data.error) return setMessage('Error: ' + data.error);
    let html = `<div class='card'><h3>Features</h3>`;
    html += `<p><strong>Numeric:</strong> ${data.numeric_features.join(', ')}</p>`;
    html += `<p><strong>Categorical:</strong> ${data.categorical_features.join(', ')}</p>`;
    if (data.strong_correlations && data.strong_correlations.length) {
        html += '<h4>Strong correlations</h4><ul>' + data.strong_correlations.map(s => `<li>${s.f1} & ${s.f2}: ${s.corr.toFixed(2)}</li>`).join('') + '</ul>';
    }
    if (data.suggestions && data.suggestions.length) { html += '<h4>Suggestions</h4><ul>' + data.suggestions.map(s => `<li>${s}</li>`).join('') + '</ul>'; }
    html += '</div>';
    outputArea.innerHTML = html;
});

// Clean - show modal-like UI inline
document.getElementById('cleanBtn').addEventListener('click', async () => {
    if (!fileUploaded) return setMessage('Upload a CSV first');
    const html = `
    <div class='card'>
      <h3>Clean Data</h3>
      <div>
        <label>Missing values:</label>
        <select id='missingMethod'>
          <option value='drop'>Drop rows</option>
          <option value='mean'>Fill numeric with mean</option>
          <option value='median'>Fill numeric with median</option>
          <option value='mode'>Fill with mode</option>
          <option value='constant'>Fill with constant</option>
          <option value='ffill'>Forward fill</option>
          <option value='bfill'>Backward fill</option>
        </select>
      </div>
      <div style='margin-top:10px'>
        <label>Constant value (if chosen):</label>
        <input id='constVal' placeholder='e.g. 0' />
      </div>
      <div style='margin-top:12px'>
        <label><input type='checkbox' id='removeDup' checked /> Remove duplicates</label><br>
        <label><input type='checkbox' id='removeEmpty' checked /> Remove empty columns</label>
      </div>
      <div style='margin-top:12px'>
        <button id='runClean' class='btn'>Run Cleaning</button>
      </div>
    </div>
  `;
    outputArea.innerHTML = html;
    document.getElementById('runClean').addEventListener('click', async () => {
        const method = document.getElementById('missingMethod').value;
        const constVal = document.getElementById('constVal').value;
        const removeDup = document.getElementById('removeDup').checked;
        const removeEmpty = document.getElementById('removeEmpty').checked;
        const payload = { remove_duplicates: removeDup, remove_empty_cols: removeEmpty, missing: { method: method } };
        if (method === 'constant') payload.missing.value = constVal;
        setMessage('Cleaning in progress...');
        const res = await fetch('/clean', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (data.error) return setMessage('Error: ' + data.error);
        let report = `<div class='card'><h3>Cleaning Report</h3><p>${data.report.summary}</p><ul>`;
        data.report.actions.forEach(a => { report += `<li>${a}</li>` });
        report += `</ul><p><button id='downloadCleaned' class='btn'>Download Cleaned CSV</button></p></div>`;
        outputArea.innerHTML = report;
        document.getElementById('downloadCleaned').addEventListener('click', () => {
            window.location.href = '/download-cleaned';
        });
    });
});

// Visualize
document.getElementById('visualizeBtn').addEventListener('click', async () => {
    if (!fileUploaded) return setMessage('Upload a CSV first');
    const html = `
    <div class='card'>
      <h3>Visualize</h3>
      
      <select id='chartType' hidden>
        <option value='auto'>Auto</option>
        
      </select>
      <div style='margin-top:12px'><button id='runViz' class='btn'>Generate ✧˖</button></div>
    </div>
  `;
    outputArea.innerHTML = html;
    document.getElementById('runViz').addEventListener('click', async () => {
        const type = document.getElementById('chartType').value;
        setMessage('Generating visualizations...');
        const res = await fetch('/visualize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: type }) });
        const data = await res.json();
        if (data.error) return setMessage('Error: ' + data.error);
        let html = `<div class='card'><h3>Visualizations</h3>`;
        data.charts.forEach(c => { html += `<div style='margin-bottom:12px'><h4>${c.title}</h4><img class='img-preview' src='${c.image}'/></div>` });
        html += '</div>';
        outputArea.innerHTML = html;
    });
});

// Download cleaned
document.getElementById('downloadBtn').addEventListener('click', () => {
    window.location.href = '/download-cleaned';
});

// Reset
document.getElementById('resetBtn').addEventListener('click', async () => {
    setMessage('Resetting dataset...');
    const res = await fetch('/reset', { method: 'POST' });
    const data = await res.json();
    if (data.success) { fileUploaded = false; uploadMsg.textContent = ''; setMessage('Session reset. Upload a new CSV.'); }
});

// support upload from landing page quick upload (if present)
(async () => {
    const lpFile = document.getElementById('lpFile');
    if (lpFile) {
        const btn = document.getElementById('lpUploadBtn');
        btn.addEventListener('click', async () => {
            const f = lpFile.files[0]; if (!f) return;
            const fd = new FormData(); fd.append('file', f);
            await fetch('/upload', { method: 'POST', body: fd });
            window.location.href = '/dashboard';
        })
    }
})();

document.getElementById('KaggleBtn').addEventListener('click', () => {
    window.open("https://www.kaggle.com/code/scratchpad/notebook093fb3f5f1/edit", "_blank");
});
