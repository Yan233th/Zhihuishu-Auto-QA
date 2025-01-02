import time
import sys
from reloading import reloading
from selenium.webdriver import Edge
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import WebDriverException
from openai import OpenAI

from secret import api_key


print("正在启动浏览器")
options = Options()
options.add_argument("--disable-logging")
options.add_argument("--log-level=OFF")
driver = Edge(service=Service(EdgeChromiumDriverManager().install(), log_path="nul"), options=options)

driver.get("https://onlineweb.zhihuishu.com/")
print("已导航至智慧树学生首页, 请自行登录")

ai_client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")


@reloading
def ask():
    try:
        if "课程问答" not in driver.title:
            print("检测到当前不在问答页, 正尝试在其他页面中查找问答页")
            all_windows = driver.window_handles
            print(all_windows)
            for window in all_windows:
                driver.switch_to.window(window)  # 逐个窗口切换
                if "课程问答" in driver.title:
                    print("成功切换到课程问答页面")
                    break
            else:
                print("未找到课程问答页面, 请打开课程问答页面")
                return
    except WebDriverException:  # 当前页已被关闭
        print("检测到当前不在问答页, 正尝试在其他页面中查找问答页")
        try:
            all_windows = driver.window_handles
        except WebDriverException:  # driver已被关闭
            print("当前浏览器已被关闭, 程序无法继续执行, 正在退出")
            driver.quit()
            sys.exit(1)
        for window in all_windows:  # 逐个窗口找
            driver.switch_to.window(window)
            if "课程问答" in driver.title:
                print("成功切换到课程问答页面")
                break
        else:
            print("未找到课程问答页面, 请打开课程问答页面")
            return

    course_name = driver.find_element(By.CLASS_NAME, "course-name").text
    print(f"课程名: {course_name}, 接下来将获取本页面前30个问题并发给AI分析")
    print("鉴于智慧树的屏蔽机制, 建议提问数量在25个以上 (20个有效问题为有效计分上限)")
    asks = int(input("请输入提问数量: "))
    print("正在获取页面中的问题并发给AI分析")
    question_elements = driver.find_elements(By.CLASS_NAME, "question-content")[:30]
    question_text = ""
    for element in question_elements:
        question_text += element.text + "\n"  # 将所有元素的文本合并
    ai_question = f"请根据提供的例子生成同领域相近但不相同的问题, 要求生成{asks}个, 以下为例子:\n" + question_text

    ai_response = ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你会收到很多问题作为样例, 你要根据提供的例子输出一定数量同领域相近但不相同的问题, 输出的问题数量将由用户指定, 输出的问题以换行分隔, 不要使用Markdown或LaTeX语法, 切记要遵循问题数量",
            },
            {"role": "user", "content": ai_question},
        ],
        temperature=0.2,
    )
    questions_list = ai_response.choices[0].message.content.split("\n")[:asks]
    print (questions_list)


@reloading
def answer():
    pass


def main():
    while True:
        print("\n选择模式: [1] [2] [3]退出程序(浏览器也会关闭)")
        mode = input("Input Mode: ")
        match mode:
            case "1":
                ask()
            case "2":
                answer()
            case "3":
                driver.quit()
                return
            case _:
                print("请输入正确的选项")


if __name__ == "__main__":
    main()
