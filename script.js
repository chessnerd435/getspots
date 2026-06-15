document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('resultsContainer');
    const loader = document.getElementById('loader');
    
    const downloadStatus = document.getElementById('downloadStatus');
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    
    const successStatus = document.getElementById('successStatus');
    const backBtn = document.getElementById('backBtn');

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (!query) return;

        // Reset UI
        resultsContainer.classList.add('hidden');
        downloadStatus.classList.add('hidden');
        successStatus.classList.add('hidden');
        loader.classList.remove('hidden');
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            const results = await response.json();
            
            loader.classList.add('hidden');
            
            if (results && results.length > 0) {
                renderResults(results);
            } else {
                alert('No results found. Try a different search term.');
            }
        } catch (err) {
            loader.classList.add('hidden');
            alert('Error searching: ' + err);
        }
    });

    function renderResults(results) {
        resultsContainer.innerHTML = '';
        results.forEach(song => {
            const card = document.createElement('div');
            card.className = 'song-card';
            
            // Clean up missing data
            const coverUrl = song.cover_url || 'https://via.placeholder.com/55';
            const artistName = song.artist || 'Unknown Artist';
            const songName = song.name || 'Unknown Track';

            card.innerHTML = `
                <div class="song-info">
                    <img src="${coverUrl}" class="song-art" alt="Cover Art">
                    <div class="song-details">
                        <h3>${songName}</h3>
                        <p>${artistName}</p>
                    </div>
                </div>
                <button class="download-icon-btn" title="Download MP3" onclick="downloadSong('${song.url}')">
                    <i class="fa-solid fa-download"></i>
                </button>
            `;
            resultsContainer.appendChild(card);
        });
        resultsContainer.classList.remove('hidden');
    }

    window.downloadSong = async (url) => {
        resultsContainer.classList.add('hidden');
        downloadStatus.classList.remove('hidden');
        progressBar.style.width = '0%';
        statusText.textContent = 'Preparing download...';

        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 4;
            if (progress > 85) progress = 85;
            progressBar.style.width = `${progress}%`;
            
            if (progress > 30) statusText.textContent = 'Downloading high quality audio...';
            if (progress > 60) statusText.textContent = 'Embedding album art and metadata...';
        }, 1000);
        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });
            
            clearInterval(progressInterval);
            
            if (response.ok && response.headers.get('content-type') === 'audio/mpeg') {
                // Read the filename from Content-Disposition if present
                let filename = 'download.mp3';
                const disposition = response.headers.get('Content-Disposition');
                if (disposition && disposition.indexOf('filename=') !== -1) {
                    const matches = /filename="([^"]*)"/.exec(disposition);
                    if (matches != null && matches[1]) { 
                        filename = matches[1];
                    }
                }

                // Get the MP3 binary stream
                const blob = await response.blob();
                
                // Create an invisible download link and click it
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                
                // Cleanup
                window.URL.revokeObjectURL(downloadUrl);
                document.body.removeChild(a);

                progressBar.style.width = '100%';
                statusText.textContent = 'Finishing up...';
                
                setTimeout(() => {
                    downloadStatus.classList.add('hidden');
                    successStatus.classList.remove('hidden');
                }, 1000);
            } else {
                const result = await response.json();
                throw new Error(result.message || 'Server error');
            }
        } catch (err) {
            clearInterval(progressInterval);
            statusText.textContent = 'Error: ' + err.message;
            progressBar.style.backgroundColor = '#ff5555';
            
            setTimeout(() => {
                downloadStatus.classList.add('hidden');
                resultsContainer.classList.remove('hidden');
                progressBar.style.backgroundColor = 'var(--accent)';
            }, 3000);
        }
    };

    backBtn.addEventListener('click', () => {
        successStatus.classList.add('hidden');
        resultsContainer.classList.remove('hidden');
        searchInput.value = '';
        searchInput.focus();
    });
});
