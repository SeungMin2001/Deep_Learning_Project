from step1_특허식 import Step1
from step2_크롤링 import Step2
from step3_필터링 import Step3
from step3_5_특허그래프 import Step3_5
from step4_벌토픽 import Step4
#from step4_1_벌토픽 import Step4_1_GTM
#from step4_2_벌토픽 import Step4_2_GTM
from step5_보고서작성 import Step5
from multiprocessing import freeze_support

def generate_report(keyword):
    try:
        print(f"Step 1: 키워드 '{keyword}'로 특허식 생성 중...")
        s1 = Step1()
        sentence = s1.make(keyword)  # keyword를 받아 특허식 생성
        print("Step 1 완료")

        print("Step 2: 특허 크롤링 중...")
        s2 = Step2()
        s2.cra(sentence)  # 특허 크롤링
        print("Step 2 완료")

        print("Step 3: 특허 필터링 중...")
        s3 = Step3()
        s3.filter()  # 특허 필터링
        print("Step 3 완료")

        print("Step 3.5: 특허 그래프 생성 중...")
        s3_5 = Step3_5()
        graph_data = s3_5.generate_graph(sentence)  # Step1에서 생성된 키워드 사용
        print("Step 3.5 완료")

        print("Step 4: 토픽 추출 중...")
        s4 = Step4()
        topic_list = s4.ber()  # 토픽 추출
        
        # s4_2=Step4_2_GTM()
        # s4_2.run_full_analysis()
        
        print("Step 4 완료")

        print("Step 5: 보고서 작성 중...")
        s5 = Step5()
        report = s5.last(topic_list)  # 보고서 작성
        print("Step 5 완료")
        
        return report
    except Exception as e:
        print(f"보고서 생성 중 오류 발생: {str(e)}")
        raise e


def main():
    # 예시 키워드 (실제 서비스에서는 웹에서 입력받음)
    keyword = input('키워드를 입력하세요: ')
    report = generate_report(keyword)
    return report

if __name__ == "__main__":
    freeze_support()
    main()


