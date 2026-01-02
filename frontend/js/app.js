/**
 * Radiology Assistant - Main Application Logic
 */

// State
let currentUser = null;
let currentAnalysis = null;

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

function initApp() {
  // Check which page we're on
  const page = document.body.dataset.page;
  
  if (page === 'login') {
    initLoginPage();
  } else if (page === 'dashboard') {
    checkAuth().then(() => initDashboard());
  } else if (page === 'analysis') {
    checkAuth().then(() => initAnalysisPage());
  }
}

async function checkAuth() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    window.location.href = 'index.html';
    return;
  }

  try {
    currentUser = await api.getCurrentUser();
    updateUserUI();
  } catch (error) {
    window.location.href = 'index.html';
  }
}

function updateUserUI() {
  const userNameEl = document.getElementById('user-name');
  const userAvatarEl = document.getElementById('user-avatar');
  const userRoleEl = document.getElementById('user-role');
  
  if (currentUser) {
    if (userNameEl) userNameEl.textContent = currentUser.full_name || currentUser.username;
    if (userAvatarEl) userAvatarEl.textContent = (currentUser.username || 'U')[0].toUpperCase();
    if (userRoleEl) userRoleEl.textContent = currentUser.role;
  }
}

// ==================== LOGIN PAGE ====================

function initLoginPage() {
  const signinForm = document.getElementById('signin-form');
  const signupForm = document.getElementById('signup-form');
  
  if (signinForm) {
    signinForm.addEventListener('submit', handleSignIn);
  }
  if (signupForm) {
    signupForm.addEventListener('submit', handleSignUp);
  }
}

async function handleSignIn(e) {
  e.preventDefault();
  
  const username = document.getElementById('signin-username').value;
  const password = document.getElementById('signin-password').value;
  const submitBtn = document.getElementById('signin-btn');
  
  hideMessage();
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px;"></span> Signing in...';

  try {
    await api.login(username, password);
    submitBtn.innerHTML = '✓ Success';
    setTimeout(() => {
      window.location.href = 'dashboard.html';
    }, 500);
  } catch (error) {
    showMessage(error.message || 'Invalid username or password', 'error');
    submitBtn.disabled = false;
    submitBtn.textContent = 'Sign In';
  }
}

async function handleSignUp(e) {
  e.preventDefault();
  
  const username = document.getElementById('signup-username').value;
  const password = document.getElementById('signup-password').value;
  const fullName = document.getElementById('signup-fullname').value;
  const email = document.getElementById('signup-email').value;
  const role = document.getElementById('signup-role').value;
  const submitBtn = document.getElementById('signup-btn');
  
  hideMessage();
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px;"></span> Creating account...';

  try {
    const result = await api.signup(username, password, fullName, email, role);
    submitBtn.innerHTML = '✓ Account Created';
    
    // Check if email was sent
    if (result.email_sent) {
      showMessage('Account created! Please check your email to verify your account.', 'success');
      setTimeout(() => {
        window.location.href = 'verify-email.html';
      }, 2000);
    } else {
      showMessage('Account created but email could not be sent. Please contact admin to verify.', 'success');
    }
  } catch (error) {
    showMessage(error.message || 'Failed to create account', 'error');
    submitBtn.disabled = false;
    submitBtn.textContent = 'Create Account';
  }
}

function showMessage(msg, type) {
  const el = document.getElementById('auth-message');
  if (el) {
    el.textContent = msg;
    el.className = `auth-message ${type}`;
  }
}

function hideMessage() {
  const el = document.getElementById('auth-message');
  if (el) {
    el.className = 'auth-message';
    el.textContent = '';
  }
}

// ==================== DASHBOARD ====================

async function initDashboard() {
  setupUploadZone();
  await loadStudies();
}

function setupUploadZone() {
  const uploadZone = document.getElementById('upload-zone');
  const fileInput = document.getElementById('file-input');
  
  if (!uploadZone || !fileInput) return;

  uploadZone.addEventListener('click', () => fileInput.click());
  
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });
  
  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
  });
  
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length) handleFileUpload(files);
  });
  
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFileUpload(e.target.files);
  });
}

async function handleFileUpload(files) {
  showLoading('Analyzing DICOM files...');
  
  try {
    const result = await api.analyzeDicom(files);
    hideLoading();
    
    if (result.status === 'completed') {
      // Store result and navigate to analysis page
      sessionStorage.setItem('analysis_result', JSON.stringify(result));
      window.location.href = 'analysis.html';
    } else {
      showToast('Analysis failed: ' + result.status, 'error');
    }
  } catch (error) {
    hideLoading();
    showToast(error.message, 'error');
  }
}

async function loadStudies() {
  const tableBody = document.getElementById('studies-table-body');
  if (!tableBody) return;

  try {
    const data = await api.listStudies();
    
    // Update all stats
    const totalStudies = data.total || data.studies.length;
    document.getElementById('total-studies').textContent = totalStudies;
    
    // Calculate stats from studies data
    const today = new Date().toDateString();
    let analyzedToday = 0;
    let pendingReview = 0;
    let urgentCases = 0;
    
    data.studies.forEach(study => {
      // Check if analyzed today (if study has timestamp)
      if (study.created_at || study.timestamp) {
        const studyDate = new Date(study.created_at || study.timestamp).toDateString();
        if (studyDate === today) {
          analyzedToday++;
        }
      }
      // Check status
      if (study.status === 'pending' || !study.status) {
        pendingReview++;
      }
      // Check urgency
      if (study.urgency === 'urgent' || study.urgency === 'emergent') {
        urgentCases++;
      }
    });
    
    // Update stat displays - use API response if available, otherwise calculated
    const analyzedTodayEl = document.getElementById('analyzed-today');
    const pendingReviewEl = document.getElementById('pending-review');
    const urgentCasesEl = document.getElementById('urgent-cases');
    
    // Prefer API-provided stats
    const apiAnalyzedToday = data.analyzed_today !== undefined ? data.analyzed_today : analyzedToday;
    const apiPending = data.pending !== undefined ? data.pending : pendingReview;
    const apiUrgent = data.urgent !== undefined ? data.urgent : urgentCases;
    
    if (analyzedTodayEl) analyzedTodayEl.textContent = apiAnalyzedToday;
    if (pendingReviewEl) pendingReviewEl.textContent = apiPending;
    if (urgentCasesEl) urgentCasesEl.textContent = apiUrgent;
    
    if (data.studies.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">No studies yet. Upload DICOM files to get started.</td></tr>';
      return;
    }

    tableBody.innerHTML = data.studies.map(study => {
      const statusBadge = study.status === 'completed' 
        ? '<span style="color:var(--success);">✓ Analyzed</span>'
        : '<span style="color:var(--warning);">Pending</span>';
      
      return `
        <tr>
          <td><code>${study.study_id.substring(0, 8)}...</code></td>
          <td>${study.file_count} files</td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn btn-glass" onclick="analyzeStudy('${study.study_id}')" style="padding:8px 16px;font-size:13px;">
              Analyze
            </button>
          </td>
        </tr>
      `;
    }).join('');
    
  } catch (error) {
    console.error('Load studies error:', error);
    if (error.message.includes('401') || error.message.includes('Session expired')) {
      // Already handled by API - will redirect
      return;
    }
    if (error.message.includes('403')) {
      tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">Insufficient permissions to view studies.</td></tr>';
    } else {
      tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">Failed to load studies. Click Refresh to try again.</td></tr>';
    }
  }
}

async function analyzeStudy(studyId) {
  showLoading('Analyzing study...');
  
  try {
    const result = await api.analyzeStudy(studyId);
    hideLoading();
    sessionStorage.setItem('analysis_result', JSON.stringify(result));
    window.location.href = 'analysis.html';
  } catch (error) {
    hideLoading();
    showToast(error.message, 'error');
  }
}

// ==================== ANALYSIS PAGE ====================

function initAnalysisPage() {
  const resultJson = sessionStorage.getItem('analysis_result');
  
  if (!resultJson) {
    window.location.href = 'dashboard.html';
    return;
  }
  
  currentAnalysis = JSON.parse(resultJson);
  renderAnalysisResults();
}

function renderAnalysisResults() {
  if (!currentAnalysis) return;
  
  // Modality
  const modalityEl = document.getElementById('modality');
  if (modalityEl) modalityEl.textContent = currentAnalysis.modality || 'Unknown';
  
  // Study ID
  const studyIdEl = document.getElementById('study-id');
  if (studyIdEl) studyIdEl.textContent = currentAnalysis.study_id;
  
  // Urgency
  const urgencyEl = document.getElementById('urgency-badge');
  if (urgencyEl && currentAnalysis.urgency) {
    urgencyEl.className = `urgency-badge ${currentAnalysis.urgency.replace('-', '')}`;
    urgencyEl.innerHTML = `<span>●</span> ${currentAnalysis.urgency.toUpperCase()}`;
  }
  
  // Findings
  const findingsContainer = document.getElementById('findings-list');
  if (findingsContainer && currentAnalysis.findings) {
    const findings = currentAnalysis.findings[0];
    const allFindings = [
      ...findings.positive_findings.map(f => ({ name: f, confidence: 0.8, positive: true })),
      ...findings.top_predictions.slice(0, 5).map(([name, conf]) => ({ name, confidence: conf, positive: conf >= 0.65 }))
    ];
    
    // Remove duplicates
    const uniqueFindings = allFindings.filter((f, i, arr) => 
      arr.findIndex(x => x.name === f.name) === i
    );
    
    findingsContainer.innerHTML = uniqueFindings.map(f => {
      const confPercent = (f.confidence * 100).toFixed(1);
      const confClass = f.confidence >= 0.7 ? 'high' : f.confidence >= 0.5 ? 'medium' : 'low';
      
      return `
        <div class="finding-item">
          <span class="finding-name">${f.name}</span>
          <div class="finding-confidence">
            <div class="confidence-bar">
              <div class="confidence-fill ${confClass}" style="width: ${confPercent}%"></div>
            </div>
            <span>${confPercent}%</span>
          </div>
        </div>
      `;
    }).join('');
  }
  
  // Report
  const reportEl = document.getElementById('report-content');
  if (reportEl && currentAnalysis.recommendations) {
    reportEl.textContent = currentAnalysis.recommendations;
  }
}

function goBack() {
  sessionStorage.removeItem('analysis_result');
  window.location.href = 'dashboard.html';
}

function printReport() {
  window.print();
}

// ==================== UTILITIES ====================

function showLoading(message = 'Loading...') {
  let overlay = document.getElementById('loading-overlay');
  
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
      <div class="spinner"></div>
      <p id="loading-message">${message}</p>
    `;
    document.body.appendChild(overlay);
  } else {
    document.getElementById('loading-message').textContent = message;
    overlay.classList.remove('hidden');
  }
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.add('hidden');
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : '!'}</span>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function logout() {
  api.logout();
}

