import csv
from myapp.models import Feedback

def export_to_csv(output_file):
    # CSV 파일 생성
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 헤더 작성
        writer.writerow(['User ID', 'Category', 'Base Type', 'Selected Tags', 'Recommendation', 'Feedback', 'Created At'])

        # 데이터베이스의 모든 데이터를 가져와 CSV에 작성
        for feedback in Feedback.objects.all():
            writer.writerow([
                feedback.user.id,
                feedback.category,
                feedback.base_type,
                feedback.selected_tags,
                feedback.recommendation,
                feedback.rating,
                feedback.created_at,
            ])
    print(f"Data exported to {output_file}")
