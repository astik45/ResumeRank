from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_resume_pdf(filename, name, role, details, skills, experience):
    os.makedirs("data/resumes", exist_ok=True)
    filepath = os.path.join("data/resumes", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Draw simple header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 750, name)
    
    c.setFont("Helvetica-Oblique", 12)
    c.drawString(50, 730, role)
    
    # Draw details
    c.setFont("Helvetica", 9)
    c.drawString(50, 715, details)
    
    # Skills section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 685, "Technical Skills")
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    c.line(50, 680, 550, 680)
    
    c.setFont("Helvetica", 9)
    y = 665
    c.drawString(60, y, ", ".join(skills))
    y -= 25
        
    # Experience section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Professional Experience")
    c.line(50, y - 5, 550, y - 5)
    y -= 20
    
    for exp in experience:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, exp["title"])
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(450, y, exp["dates"])
        y -= 12
        
        c.setFont("Helvetica", 9)
        for bullet in exp["bullets"]:
            c.drawString(65, y, f"- {bullet}")
            y -= 12
        y -= 10
        
    c.save()
    print(f"Created: {filepath}")

if __name__ == "__main__":
    # 1. Backend Resume
    create_resume_pdf(
        "alice_backend_engineer.pdf",
        "Alice Smith",
        "Senior Python & Backend Engineer",
        "Email: alice@example.com | GitHub: github.com/alice | LinkedIn: linkedin.com/in/alice",
        ["Python", "FastAPI", "Django", "PostgreSQL", "RESTful APIs", "SQL", "Docker", "Database Design"],
        [
            {
                "title": "Senior Backend Developer at TechCorp",
                "dates": "2022 - Present",
                "bullets": [
                    "Designed and implemented high-throughput REST APIs using FastAPI and PostgreSQL, reducing latency by 35%.",
                    "Optimized complex database queries and SQL schemas, reducing average response time from 300ms to 80ms.",
                    "Collaborated with frontend developers to design clean API contracts and integrate payment gateways."
                ]
            },
            {
                "title": "Backend Engineer at SoftSolutions",
                "dates": "2019 - 2022",
                "bullets": [
                    "Developed backend services and business logic for web applications using Django and Python.",
                    "Maintained background workers and task queues using Celery and Redis."
                ]
            }
        ]
    )

    # 2. Frontend Resume
    create_resume_pdf(
        "bob_frontend_developer.pdf",
        "Bob Jones",
        "Lead React Frontend Developer",
        "Email: bob@example.com | Portfolio: bob.dev | GitHub: github.com/bob",
        ["React", "JavaScript", "TypeScript", "HTML5", "CSS3", "TailwindCSS", "Redux", "UI/UX Design"],
        [
            {
                "title": "Lead Frontend Engineer at DesignHub",
                "dates": "2023 - Present",
                "bullets": [
                    "Architected and developed modular frontend components using React and TypeScript.",
                    "Created highly responsive UI designs with modern layouts styled using TailwindCSS.",
                    "Improved core web vitals and overall web app performance by lazy-loading components."
                ]
            },
            {
                "title": "Frontend Developer at PixelPerfect",
                "dates": "2020 - 2023",
                "bullets": [
                    "Built interactive, user-facing web features using Vanilla JavaScript and CSS.",
                    "Worked directly with UI/UX designers to translate Figma mockups into pixel-perfect code."
                ]
            }
        ]
    )

    # 3. Cloud / DevOps Resume
    create_resume_pdf(
        "charlie_cloud_devops.pdf",
        "Charlie Green",
        "Cloud Architect & DevOps Engineer",
        "Email: charlie@example.com | AWS Certified | GitHub: github.com/charlie",
        ["AWS", "Docker", "Kubernetes", "DevOps", "CI/CD Pipelines", "Terraform", "GitHub Actions", "Linux"],
        [
            {
                "title": "DevOps Architect at CloudScale Solutions",
                "dates": "2021 - Present",
                "bullets": [
                    "Provisioned scalable multi-region AWS cloud infrastructure using Terraform (IaC).",
                    "Managed containerized production workloads on Kubernetes (EKS) and Docker.",
                    "Implemented zero-downtime rolling deployments and service meshes for microservices."
                ]
            },
            {
                "title": "Cloud Operations Engineer at InfraSolutions",
                "dates": "2018 - 2021",
                "bullets": [
                    "Created and automated CI/CD pipelines using GitHub Actions and Jenkins, cutting deploy times by 50%.",
                    "Monitored server health, infrastructure logs, and alerts using Prometheus and Grafana."
                ]
            }
        ]
    )

    # 4. AI / ML Resume
    create_resume_pdf(
        "diana_ai_ml_scientist.pdf",
        "Diana Prince",
        "Machine Learning & NLP Research Scientist",
        "Email: diana@example.com | PhD in Data Science | Scholar: scholar.diana",
        ["Machine Learning", "PyTorch", "TensorFlow", "NLP", "Large Language Models", "Deep Learning", "Python", "Data Science"],
        [
            {
                "title": "Senior ML Scientist at AI Labs",
                "dates": "2022 - Present",
                "bullets": [
                    "Researched and built document retrieval pipelines utilizing vector embeddings and LLM generation.",
                    "Fine-tuned transformer models using PyTorch for natural language parsing and categorization tasks.",
                    "Published 3 papers on semantic search efficiency and retrieval augmented generation (RAG)."
                ]
            },
            {
                "title": "Data Scientist at AnalyticsCorp",
                "dates": "2019 - 2022",
                "bullets": [
                    "Trained, validated, and deployed predictive classification models using Scikit-Learn and Pandas.",
                    "Cleaned unstructured customer feedback text data for sentiment analysis algorithms."
                ]
            }
        ]
    )
