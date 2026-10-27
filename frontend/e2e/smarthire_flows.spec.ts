import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCREENSHOT_DIR = path.resolve(__dirname, '../../reports/screenshots');
const SYNTHETIC_RESUME_PATH = path.resolve(__dirname, 'fixtures/synthetic_resume.txt');
const TEMPORARY_RESUME_PATH = path.resolve(__dirname, 'fixtures/temporary_resume.txt');

test.describe('SmartHire 2.0 Browser E2E Test Suite', () => {

  test('01 - Candidate E2E Journey: Auth, Resume Upload, Extraction, Recommendations, Match Details, Profile Edit, Deletion, and RBAC Block', async ({ page }) => {
    const timestamp = Date.now();
    const candidateEmail = `candidate_e2e_${timestamp}@example.com`;
    const candidatePassword = 'Password123!';

    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', err => consoleErrors.push(err.message));

    // 1. Visit Auth Page and switch to Register
    await page.goto('/auth');
    await expect(page.locator('h2')).toContainText('Sign in to your account');

    await page.getByRole('button', { name: 'Register now' }).click();
    await expect(page.locator('h2')).toContainText('Create your SmartHire account');

    // 2. Fill registration form as Candidate
    await page.locator('#fullname').fill('Alice Candidate E2E');
    await page.getByRole('button', { name: 'Candidate' }).click();
    await page.locator('#email').fill(candidateEmail);
    await page.locator('#password').fill(candidatePassword);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_auth_register_candidate.png'), fullPage: true });

    // 3. Submit registration
    await page.locator('button[type="submit"]').click();

    // 4. Assert arrival at Candidate Dashboard
    await page.waitForURL('**/dashboard');
    await expect(page.locator('h1')).toContainText('Welcome back, Alice Candidate E2E');
    await expect(page.getByText('Candidate Portal Active')).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_candidate_dashboard.png'), fullPage: true });

    // 5. Navigate to Resume Analyzer
    await page.getByRole('link', { name: 'Analyze Resume' }).first().click();
    await page.waitForURL('**/resumes/analyze');
    await expect(page.locator('h1')).toContainText('Resume Parser & NLP Classifier');

    // 6. Upload synthetic resume
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('label[for="resume-file"]').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(SYNTHETIC_RESUME_PATH);

    await expect(page.getByText('Selected:')).toBeVisible();

    // 7. Click Run Analysis
    await page.getByRole('button', { name: 'Run Analysis' }).click();

    // 8. Assert verification fingerprint, predicted category, and skills
    await expect(page.getByText('Verification Fingerprint')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Predicted Job Category')).toBeVisible();
    await expect(page.getByText('Model Confidence:')).toBeVisible();
    await expect(page.getByText('Extracted Technical Skills')).toBeVisible();

    // Verify at least one skill pill (e.g. Python)
    await expect(page.locator('span:has-text("Python"), span:has-text("python")').first()).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_resume_analyzer_parsed.png'), fullPage: true });

    // 9. Inspect Job Recommendations section
    await expect(page.getByText('Top Ranked Job Recommendations for this Resume')).toBeVisible();
    const detailsButtons = page.getByRole('button', { name: /Details/i });
    await expect(detailsButtons.first()).toBeVisible();

    // 10. Click Details on the top recommended job
    await detailsButtons.first().click();

    // 11. Assert Match Details Page & 3-Factor Heuristic Scores
    await page.waitForURL('**/matching?**');
    await expect(page.locator('h1')).toContainText('Job Match Compatibility Details');
    await expect(page.locator('#resume-text-input')).not.toBeEmpty();
    await expect(page.locator('#job-description-input')).not.toBeEmpty();

    await expect(page.getByText('Overall Alignment')).toBeVisible();
    await expect(page.getByText('Text Similarity (50%)')).toBeVisible();
    await expect(page.getByText('Skill Overlap (30%)')).toBeVisible();
    await expect(page.getByText('Experience Match (20%)')).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_job_match_details.png'), fullPage: true });

    // 12. Candidate Profile Editing via Settings
    await page.goto('/settings');
    await expect(page.locator('h1')).toContainText('Settings & Account Profile');
    await expect(page.locator('main').getByText('Alice Candidate E2E').first()).toBeVisible();

    await page.getByRole('button', { name: 'Edit Profile' }).click();
    await expect(page.locator('#edit-fullname')).toBeVisible();
    await page.locator('#edit-fullname').fill('Alice Candidate E2E Updated');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    await expect(page.getByText('Profile name updated successfully.')).toBeVisible();
    await expect(page.locator('main').getByText('Alice Candidate E2E Updated').first()).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_candidate_profile_edited.png'), fullPage: true });

    // 13. Candidate Resume Deletion Workflow
    // Upload a temporary resume
    await page.goto('/resumes/analyze');
    const tempFileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('label[for="resume-file"]').click();
    const tempFileChooser = await tempFileChooserPromise;
    await tempFileChooser.setFiles(TEMPORARY_RESUME_PATH);
    await page.getByRole('button', { name: 'Run Analysis' }).click();
    await expect(page.getByText('Verification Fingerprint')).toBeVisible({ timeout: 15000 });

    // Navigate to Dashboard to inspect portfolio
    await page.goto('/dashboard');
    await expect(page.getByText('Your Uploaded Resumes')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'temporary_resume.txt' })).toBeVisible();

    // Accept delete confirmation dialog
    page.once('dialog', async dialog => {
      expect(dialog.message()).toContain('Are you sure you want to delete this resume?');
      await dialog.accept();
    });

    const deleteBtn = page.getByRole('button', { name: 'Delete temporary_resume.txt' });
    await deleteBtn.click();

    await expect(page.getByText('Resume document deleted successfully.')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'temporary_resume.txt' })).toHaveCount(0);
    await expect(page.getByRole('heading', { name: 'synthetic_resume.txt' })).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_candidate_resume_deleted.png'), fullPage: true });

    // 14. Authorization Boundary: Candidate attempting recruiter route
    await page.goto('/recruiter/candidates');
    await expect(page.getByText('403 Forbidden')).toBeVisible();
    await expect(
      page.getByText('Operation requires recruiter or administrator privileges. Candidate accounts cannot view recruiter records.')
    ).toBeVisible();
    await expect(page.locator('tbody tr')).toHaveCount(0);

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_authorization_failure_blocked.png'), fullPage: true });

    // Sign out
    await page.goto('/settings');
    await page.getByRole('button', { name: 'Sign Out' }).first().click();
    await page.waitForURL('**/');

    const fatalErrors = consoleErrors.filter(e => !e.includes('favicon'));
    expect(fatalErrors).toHaveLength(0);
  });

  test('02 - Recruiter E2E Journey: Registration, Dashboard Metrics, Candidate Inspection, Shortlist & Decline Actions', async ({ page }) => {
    const timestamp = Date.now();
    const recruiterEmail = `recruiter_e2e_${timestamp}@example.com`;
    const recruiterPassword = 'Password123!';

    // 1. Register as Recruiter
    await page.goto('/auth');
    await page.getByRole('button', { name: 'Register now' }).click();
    await page.locator('#fullname').fill('Bob Recruiter E2E');
    await page.getByRole('button', { name: 'Recruiter' }).click();
    await page.locator('#email').fill(recruiterEmail);
    await page.locator('#password').fill(recruiterPassword);
    await page.locator('button[type="submit"]').click();

    // 2. Verify Recruiter Dashboard
    await page.waitForURL('**/recruiter/dashboard');
    await expect(page.locator('h1')).toContainText('Recruiter Command Center');
    await expect(page.getByText('Total Ingested Candidates')).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_recruiter_dashboard.png'), fullPage: true });

    // 3. Navigate to Candidate Management
    await page.goto('/recruiter/candidates');
    await expect(page.locator('h1')).toContainText('Candidate Pipeline & Management');

    // Wait for candidate rows to load
    const candidateRows = page.locator('tbody tr');
    await expect(candidateRows.first()).toBeVisible({ timeout: 15000 });

    // 4. Click Inspect on a candidate row
    await page.getByRole('button', { name: 'Inspect' }).first().click();

    // 5. Assert modal contents: skills & sanitized text
    await expect(page.getByText('Candidate Profile Inspection')).toBeVisible();
    await expect(page.getByText(/Extracted Technical Skills/i)).toBeVisible();
    await expect(page.getByText('PII-Sanitized Text Preview')).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09_recruiter_candidate_inspected.png'), fullPage: true });

    // Close modal
    await page.locator('button:has-text("Close"), button[aria-label="Close"], button:has(svg.lucide-x)').first().click();

    // 6. Shortlist candidate action
    const shortlistBtn = page.getByRole('button', { name: 'Shortlist' }).first();
    await shortlistBtn.click();

    await expect(page.getByText(/Candidate shortlisted successfully/i)).toBeVisible();
    await expect(page.getByText('Shortlisted').first()).toBeVisible();

    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10_recruiter_candidate_shortlisted.png'), fullPage: true });

    // 7. Decline / Reject candidate action
    const declineButtons = page.getByRole('button', { name: 'Decline' });
    if (await declineButtons.count() > 0) {
      await declineButtons.first().click();
      await expect(page.getByText(/Candidate flagged as declined successfully/i)).toBeVisible();
      await expect(page.getByText('Declined').first()).toBeVisible();
    }

    // Sign out
    await page.goto('/settings');
    await page.getByRole('button', { name: 'Sign Out' }).first().click();
    await page.waitForURL('**/');
  });

  test('03 - Unauthenticated Direct Access Guard: Redirects to /auth', async ({ page }) => {
    // Direct unauthenticated navigation to protected /dashboard
    await page.goto('/dashboard');
    await page.waitForURL('**/auth');
    await expect(page.locator('h2')).toContainText('Sign in to your account');
  });
});
