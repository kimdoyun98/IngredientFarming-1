# IngredientFarming

<img width="758" height="451" alt="Image" src="https://github.com/user-attachments/assets/2add9b73-ccd3-4928-813b-741ab764d6d9" />

## 프로젝트 소개
냉장고 또는 부엌의 수납장을 열어보면 언제 산 지 기억도 나지 않는 유통기한이 지난 식재료를 발견할 때가 많다.   
방치되는 식재료를 미연에 방지하고자 식재료를 관리하여 유통기한이 얼마 남지 않은 재료를 사용자에게 알려주고, 나만의 레시피를 저장하여 보유 중인 식재료로 만들 수 있는 레시피를 추천해주는 서비스


<br>  

## 핵심 기능

- 식재료를 저장
    - 바코드를 촬영하여 저장
    - 직접 식재료에 대한 정보를 입력하여 저장
- 식재료 관리
    - 유통기한 임박 시 홈 화면에 표시
- 장보기
    - 부족한 식재료를 추가하여 마트에서 쉽게 장을 볼 수 있도록 관리
 
<br>

## Tech Stack    
`Kotlin`, `Compose`, `MVI`, `Clean Architecture`, `build-logic`, `Retrofit2`, `Kotlinx-Serialization`, `Coroutine` , `Flow` , `Hilt` , `Room`, `GithubActions` , `Gemini`
<br>
* build logic
    * 멀티 모듈에서 각각의 모듈에 사용되는 gradle을 하나로 관리하고 유지보수하기 위함
    * plugin을 통해 쉽게 사용할 수 있음
* Hilt
    * 멀티 모듈에서 어노테이션으로 쉽게 의존성 주입
    * 의존성 그래프를 통해 어디서 주입 받는지 쉽게 추적 가능
* Compose
    * 선언형 UI로 UI 상태 값 변화에 따른 UI 변경 테스트를 Preview를 통해 빠르게 테스트할 수 있음
    * Adapter와 같은 부가적인 클래스 객체가 필요하지 않은 점
    * 이러한 점들이 생산성을 높여주기 때문에 사용
* MVI
    * 호이스팅으로 데이터를 전달하는 컴포즈의 특성 상 스크린에 기능이 많아지면 전달 할 매개 변수 또한 많아짐
    * 이러한 이유로 유지보수 측면에서 어려움이 있을 수 있음
    * MVI는 사용자의 Action에 대해 Intent로 전달 받고, Intent에 따른 작업을 한 곳에서 관리하기 때문에 유지보수가 쉬워짐
 

<br>    

## 개발 기간
2026.02 ~ 현재
* 식재료 저장
  * 바코드를 촬영하여 바코트 상품 정보 가져오기
  * 직접 입력하여 저장
* 식재료 관리
  * 유통기한 임박 식재료는 홈 화면 및 빨간색으로 UI 표시
  * 카테고리 별 관리
* 장보기
  * 필요한 식재료 추가
  * 구입 완료 식재료는 자동으로 식재료 저장하여 관리

 <br>

## Issue

### 1. Stability Configuration File로 모듈 간 객체 Stability 안정화

- 문제
    - 다른 모듈의 데이터 클래스를 사용하면 해당 데이터 클래스가 Stable 타입이어도 이를 사용하는 Composable 함수는 Unstable
    - Stable Type이 unstable인 경우 불필요한 Recomposition이 발생할 위험이 높다.
    
- 문제 해결
    ```kotlin
    implementation("androidx.compose.runtime:runtime")
    ```
    - 1차로 `@Immutable` , `@Stable` 어노테이션으로 Stable Type 변경을 하였으나, 어노테이션을 사용하기 위해 안드로이드 의존성이 추가,     
    또한 해당 데이터 클래스를 사용하는 모듈에도 안드로이드 의존성이 강제되는 문제 발생
    - 2차로 어노테이션을 제거한 뒤 Stability Contiguration File에 데이터 클래스를 정의하여 Stable Type 보장
- 결과
    - 어노테이션을 사용하지 않아 안드로이드 의존성이 강제되지 않고 Stable Type을 유지



### 2. BackStack으로 ViewModel 데이터 유지

- 문제
    - 식재료 추가 로직은 식재료 정보 입력 → 입력한 식재료 목록 → 식재료 추가 또는 저장
    - 식재료 목록에서 식재료를 추가하여 화면이 전환되어도 식재료 목록의 데이터는 유지되어야 한다.
- 해결
    - 식재료 목록 화면은 BackStack에서 사라지거나 추가되지 않고 하나의 BackStack으로 유지되어야 한다.
    - 목록에서 추가 화면으로 넘어가도 목록 화면은 BackStack에서 유지
    - 추가 후 목록 화면으로 넘어갈 때, 새로운 목록 화면을 생성하여 백스택에 추가하면 기존의 데이터가 사라지기 때문에 `launchSingleTop = true` 을 통해 BackStack에 있는 목록 화면을 가져온다.
- 결과
    - 추가 화면에서 목록으로 넘어갈 때, 추가 화면은 BackStack에서 제거되고 BackStack의 목록 화면을 가져온다.
    - 추가된 식재료들의 목록이 사라지지 않고 유지되며, 이를 통해 여러 식재료를 한 번에 저장할 수 있다.


<br>

## 자동화

### 1. AI PR 리뷰 자동화
<img width="917" height="512" alt="Image" src="https://github.com/user-attachments/assets/91f31d3e-557c-48ce-aa60-9b67a02ac009" />   

- 개인 프로젝트를 진행하면서 코드 개선을 하고 싶은 상황에서 매번 코드를 복사하여 AI에게 물어보는 과정이 반복
- GithubActions와 Gemini를 이용해 PR을 올리면 자동으로 AI가 PR 리뷰를 달아주는 로직 구현

#### 제한 된 토큰을 얼마나 효율적으로 사용하는가?
- 요청 프롬프트 최소화
    - 전체적인 코드에 대한 리뷰가 아닌 아키텍처와 Compose 위주의 리뷰 범위 축소
    - 파일명을 통해 핵심 파일만 추출 ex) *UseCase, *RepositoryImpl, *Screen
    - 파일 내의 변경 된 코드 중 키워드를 통해 핵심 코드만 추출 ex) suspend, when, if, flow 등
- 응답 최소화
    - 서론 생략 및 문제와 개선 방향 위주로 간략하게 요청

### 2. CI/CD
당연히 레포지토리에 Push하는 경우 빌드 후 안전이 확인되면 Push하는게 당연하지만, 사람은 실수를 하기 마련이다. 리팩토링 시 간혹가다 빌드를 생략하고 Push 또는 Merge하는 경우를 미연에 방지하고자 PR을 올리면 빌드 & 테스트를 자동으로 수행하여 PR 단계에서 문제를 검출하도록 구현

- GithubActions를 사용하여 PR이 올라오면 Build 및 테스트 자동 진행
- 아직 구현 단계로 배포는 미작성





