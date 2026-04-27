import os
import requests
import random
import time
from typing import List, Dict
from google import genai

class GeminiCodeReview2:
    def __init__(self):
        # -------------------------
        # 환경 변수
        # -------------------------
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.pr_number = os.getenv("PR_NUMBER")
        self.repo = os.getenv("GITHUB_REPOSITORY")

        # -------------------------
        # 우선순위
        # -------------------------
        self.priority = {
            "domain": 1,
            "presentation_vm": 2,
            "presentation_ui": 3
        }

        if not all([self.github_token, self.api_key, self.pr_number, self.repo]):
            raise ValueError("환경 변수가 제대로 설정되지 않았습니다.")

    # -------------------------
    # 1. PR 파일 가져오기
    # -------------------------
    def get_pr_files(self) -> List[Dict]:
        files = []
        page = 1
    
        while True:
            url = f"https://api.github.com/repos/{self.repo}/pulls/{self.pr_number}/files?per_page=100&page={page}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
    
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                raise Exception(f"PR 파일 조회 실패: {res.text}")
    
            data = res.json()
            if not data:
                break
    
            files.extend(data)
            page += 1
    
        return files

    # -------------------------
    # 2. 파일 분류
    # -------------------------
    def classify_file(self, file_path: str) -> str:
        print(f"file_path: {file_path}")
        
        if file_path.endswith("UseCase.kt"):
            return "domain"
        elif file_path.endswith("RepositoryImpl.kt"):
            return "data"
        elif file_path.endswith("ViewModel.kt"):
            return "presentation_vm"
        elif file_path.endswith("Screen.kt"):
            return "presentation_ui"
        else:
            return "ignore"

    # -------------------------
    # 3. 의미 있는 Diff 추출
    # -------------------------
    def extract_meaningful_diff(self, patch: str) -> str:
        if not patch:
            return ""

        keywords = [
            "if", "when", "for", "while",
            "return",
            "suspend",
            "Flow",
            "collect",
            "launch",
            "emit",
            "="
        ]

        lines = patch.split("\n")
        filtered = []

        for line in lines:
            if line.startswith("+") or line.startswith("-"):
                if any(k in line for k in keywords):
                    filtered.append(line)

        return "\n".join(filtered)

    # -------------------------
    # 4. Chunk 분리
    # -------------------------
    def split_chunks(self, code: str, max_size: int = 1500) -> List[str]:
        return [code[i:i + max_size] for i in range(0, len(code), max_size)]

    # -------------------------
    # 5. 한글 프롬프트
    # -------------------------
    def build_prompt(self, code: str, category: str) -> str:
        base = """
            당신은 시니어 안드로이드 개발자입니다.
            
            아래 규칙에 따라 코드 리뷰를 진행하세요.
            서론은 생략하고 문제와 개선 방향을 간결하게 지적하세요.
            불필요한 설명, 칭찬, 요약은 하지 마세요.
        """

        if category == "domain":
            rule = """
                [Domain 리뷰]
                - 비즈니스 로직이 올바른지
                - Domain 책임 위반 여부
            """
        elif category == "data":
            rule = """
                [Data 리뷰]
                - 클린 아키텍처의 Data 모듈에 대한 경계와 책임 위반 여부
            """
        elif category == "presentation_vm":
            rule = """
                [ViewModel 리뷰]
                - 상태 관리 문제
                - Coroutine / Flow 오용
            """
        elif category == "presentation_ui":
            rule = """
                [Compose 리뷰]
                - 잘못된 Compose 사용
                - recomposition 문제
                - state hoisting 문제
            """
        else:
            return None

        return base + rule + "\n\n[코드]\n" + code

    def retry_with_backoff(self, func, max_retries=5, base_delay=1):
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                is_last = attempt == max_retries - 1

                # 503 / UNAVAILABLE 같은 경우만 retry
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if is_last:
                        raise

                    delay = base_delay * (2 ** attempt)
                    jitter = random.uniform(0, 0.5)  # thundering herd 방지
                    sleep_time = delay + jitter

                    print(f"⚠️ Gemini 과부하, {sleep_time:.2f}s 후 재시도 ({attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    # 다른 에러는 바로 실패
                    raise

    # -------------------------
    # 6. Gemini 호출
    # -------------------------
    def call_gemini(self, prompt: str) -> str:
        client = genai.Client(api_key=self.api_key)

        def request():
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )

            return getattr(response, "text", "❌ AI 응답 없음")

        return self.retry_with_backoff(request)

    # -------------------------
    # 7. GitHub PR 코멘트 작성
    # -------------------------
    def create_review_comment(self, review):
        url = f"https://api.github.com/repos/{self.repo}/issues/{self.pr_number}/comments"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "body": f"## 🤖 AI Code Review\n\n{review}"
        }

        res = requests.post(url, headers=headers, json=data)

        if res.status_code != 201:
            raise Exception(f"PR 코멘트 등록 실패: {res.text}")

    # -------------------------
    # 8. 메인 실행
    # -------------------------
    def run(self):
        print("🚀 AI 코드 리뷰 시작")
        files = self.get_pr_files()
        print(f"✅ 파일 가져오기 완료 \n {files}\n")
        filtered = []

        # 1차 필터
        for f in files:
            category = self.classify_file(f["filename"])

            if category == "ignore":
                continue

            if f.get("additions", 0) + f.get("deletions", 0) < 5:
                continue

            print(f"Filtered Append: category - {category}, file - {f}")
            filtered.append((category, f))

        # 우선순위 정렬
        filtered.sort(key=lambda x: self.priority.get(x[0], 999))

        print(f"✅ 파일 필터 완료 / 결과: {len(filtered)}개")

        all_reviews = []

        # 리뷰 실행
        for category, file in filtered:
            diff = self.extract_meaningful_diff(file.get("patch", ""))
            if not diff.strip():
                continue

            chunks = self.split_chunks(diff)
            for i, chunk in enumerate(chunks):
                prompt = self.build_prompt(chunk, category)

                if not prompt:
                    print("❌ Not Prompt")
                    continue

                review = self.call_gemini(prompt)
                file_name = file["filename"].split("/")[-1]

                all_reviews.append(f"### 📄 {file_name}\n{review}")

        print(f"✅ Gemini 코드 리뷰 완료 / 리뷰 개수: {len(all_reviews)}개")

        # 결과 코멘트 작성
        if all_reviews:
            final_comment = "\n\n".join(all_reviews)
            self.create_review_comment(final_comment)
            print("✅ PR 코멘트 작성 완료")
        else:
            print("🚀 리뷰가 없습니다.")


# -------------------------
# 실행
# -------------------------
if __name__ == "__main__":
    GeminiCodeReview2().run()
