class FuturesPredictor {
    constructor() {
        this.form = document.getElementById('predictionForm');
        this.resultsSection = document.getElementById('resultsSection');
        this.apiUrl = 'http://localhost:3001/api/predict';
        this.collegePredictorUrl = 'http://localhost:3001';
        this.currentResult = null;
        this.init();
    }

    async init() {
        await this.loadConfig();
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.addInputValidation();
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/futures/config');
            if (response.ok) {
                const config = await response.json();
                this.apiUrl = config.futures_api_url;
                this.collegePredictorUrl = config.college_predictor_url;
            } else {
                // Fallback to default URLs if config fails
                this.apiUrl = 'http://localhost:3001/api/predict';
                this.collegePredictorUrl = 'http://localhost:3001';
            }
        } catch (error) {
            console.error('Failed to load config:', error);
            // Fallback to default URLs
            this.apiUrl = 'http://localhost:3001/api/predict';
            this.collegePredictorUrl = 'http://localhost:3001';
        }
    }

    addInputValidation() {
        const marksInput = document.getElementById('jeeMarks');
        marksInput.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            if (value >= 300) e.target.value = 300;
            if (value <= -75) e.target.value = -75;
        });
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = this.getFormData();
        if (!this.validateForm(formData)) return;

        this.showLoading(true);

        try {
            const result = await this.predict(formData);
            this.displayResults(result);
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.showLoading(false);
        }
    }

    getFormData() {
        return {
            marks: parseInt(document.getElementById('jeeMarks').value),
            category: this.mapCategoryToAPI(document.getElementById('category').value)
        };
    }

    mapCategoryToAPI(frontendCategory) {
        const mapping = {
            'General (GEN)': 'GEN',
            'OBC': 'OBC',
            'SC': 'SC',
            'ST': 'SC', // Map ST to SC as API only supports GEN, OBC, SC
            'EWS': 'GEN' // Map EWS to GEN as API only supports GEN, OBC, SC
        };
        return mapping[frontendCategory] || 'GEN';
    }

    validateForm(data) {
        if (!data.marks || data.marks < -75 || data.marks > 300) {
            this.showError('Please enter valid JEE marks (-75 to 300)');
            return false;
        }
        if (!data.category) {
            this.showError('Please select a category');
            return false;
        }
        return true;
    }

    async predict(data) {
        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Prediction failed');
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error('Prediction failed');
        }

        return result;
    }

    displayResults(result) {
        console.log('displayResults called with:', result);
        const prediction = result.prediction;
        this.currentResult = result; // Store current result for college predictor

        // Update result values using the API response structure
        document.getElementById('resultMarks').textContent = prediction.marksOutOf300;
        document.getElementById('resultPercentile').textContent = `${prediction.percentile.toFixed(3)}%`;
        document.getElementById('resultAllIndiaRank').textContent = this.formatNumber(prediction.air);
        document.getElementById('resultCategoryRank').textContent = this.formatNumber(prediction.categoryRank);

        // Update category rank label
        const categoryShort = prediction.category;
        document.getElementById('categoryRankLabel').textContent = `${categoryShort} Rank`;

        // Update status badge
        const statusBadge = document.getElementById('statusBadge');
        const scorePercentage = prediction.scorePercentage.toFixed(2);
        statusBadge.innerHTML = `<i class="fas fa-check-circle"></i> ${scorePercentage}% Score`;

        // Show results with animation
        this.resultsSection.style.display = 'block';
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });

        // Update the View Colleges button URL with actual rank and category
        this.updateViewCollegesButton(prediction);
    }

    updateViewCollegesButton(prediction) {
        const button = document.getElementById('viewCollegesBtn');
        if (button) {
            // Map category from API format to college predictor format
            const categoryMapping = {
                'GEN': 'OPEN',
                'OBC': 'OBC',
                'SC': 'SC'
            };

            const mappedCategory = categoryMapping[prediction.category] || 'OPEN';
            const baseUrl = this.collegePredictorUrl || 'http://localhost:3001';

            const params = new URLSearchParams({
                exam: 'JoSAA',
                rank: prediction.air,
                code: 'JoSAA',
                category: mappedCategory,
                gender: 'Gender-Neutral',
                program: 'Engineering',
                homeState: 'Delhi',
                preferHomeState: 'Yes',
                qualifiedJeeAdv: 'No',
                mainRank: prediction.air
            });

            const url = `${baseUrl}/college_predictor?${params.toString()}`;
            button.onclick = () => window.open(url, '_blank');
        }
    }

    formatNumber(num) {
        return num.toLocaleString('en-IN');
    }

    getCategoryShort(category) {
        const mapping = {
            'General (GEN)': 'GEN',
            'OBC': 'OBC',
            'SC': 'SC',
            'ST': 'ST',
            'EWS': 'EWS'
        };
        return mapping[category] || 'GEN';
    }

    showLoading(show) {
        const button = this.form.querySelector('.predict-btn');
        if (show) {
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Predicting...';
            button.disabled = true;
        } else {
            button.innerHTML = '<i class="fas fa-magic"></i> Predict My Results';
            button.disabled = false;
        }
    }

    showError(message) {
        // Create or update error element
        let errorEl = document.getElementById('errorMessage');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.id = 'errorMessage';
            errorEl.style.cssText = `
                background: #f8d7da;
                color: #721c24;
                padding: 12px;
                border-radius: 8px;
                margin: 15px 0;
                border: 1px solid #f5c6cb;
            `;
            this.form.appendChild(errorEl);
        }

        errorEl.textContent = message;
        setTimeout(() => errorEl.remove(), 5000);
    }
}

// Initialize the predictor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FuturesPredictor();
});
