# -*- coding: UTF-8 -*-
import re
from random import sample, choice, shuffle
from difflib import get_close_matches as alike
import os



class Game:
    def __init__(self, start, finish):
        self.sections = {}
        self.vocab = {}
        self.mastered = set()
        self.studylist = set()
        self._getStudyRecord()
        self.start = start
        self.finish = finish

        sections_temp = {}
        with open("synonyms.txt", "r", encoding='utf-8') as f:
            currSection = []
            f.readline()
            c = 0
            for line in f:
                # print(line)
                if line.strip('\n').strip('\t') == '':
                    if len(currSection) <= 1:
                        continue
                    title, content = self._parseSection(currSection)
                    if c >= self.start and c < self.finish:
                        for item in content:
                            self.vocab[item[0]] = (item[1], item[2])
                        sections_temp[title] = content
                        currSection = []
                    c += 1
                else:
                    currSection.append(line)

        for group in sections_temp:
            poses = {}
            poses['n.'] = []
            poses['v.'] = []
            poses['a.'] = []
            for word in sections_temp[group]:
                pos = word[1]
                if 'n' in pos:
                    poses['n.'].append(word)
                if 'v' in pos:
                    poses['v.'].append(word)
                if 'a' in pos:
                    poses['a.'].append(word)
            self.sections[group] = poses

    def _getStudyRecord(self):
        with open("mastered.txt", "r+") as f:
            for line in f:
                word = line.strip('\n').strip('\t')
                if word:
                    self.mastered.add(word)
        with open("studylist.txt", "r+") as f:
            for line in f:
                word = line.strip('\n').strip('\t')
                if word:
                    self.studylist.add(word)

    def _getWordsInSection(self, sec):
        words = set()
        for pos in sec:
            for item in sec[pos]:
                words.add(item[0])
        return words

    def _parseSection(self, section):
        words = []
        title = ""
        if len(section) > 0:
            title = section[0].strip("\n").strip()
            for i in range(1, len(section)):
                # found = re.findall(r"([\w\-]+)\s+" + r"((?:[a-zA-Z\.]+)+)" + r"([^a-zA-z\.]+?)[\s|\n]", section[i])
                found = re.findall(r"([a-zA-Z\-]+)\s+" + "((?:[adjvnit\\\.]+)+)(.+?)[\||\n\r]", section[i])
                words += found
        return title, words

    def _getSimilarWords(self, sec1, answer):
        incorrect = set()
        vocab_word = self.vocab.keys()
        samegroup = self._getWordsInSection(sec1)
        for i in answer:
            similar = alike(i, vocab_word, n=3)
            for word in similar:
                if word not in samegroup | self.mastered:
                    incorrect.add((word, self.vocab[word][0], self.vocab[word][1]))
        return list(incorrect)

    def _getRandomWords(self, keys):
        sec2 = self.sections[keys[1]]
        pos2 = choice(list(sec2.values()))
        while len(pos2) < 2:
            pos2 = choice(list(sec2.values()))
        incorrect = sample(pos2, 2)

        sec3 = self.sections[keys[2]]
        pos3 = choice(list(sec3.values()))
        while len(pos3) < 2:
            pos3 = choice(list(sec3.values()))
        incorrect += sample(pos3, 2)
        return incorrect

    def _getUnstudiedWord(self, pos):
        unstudied = set()
        for item in pos:
            if item[0] not in self.mastered:
                unstudied.add(item)
        return list(unstudied)


    def getChoices(self):
        while True:
            keys = sample(list(self.sections.keys()), 3)
            chosenSec = self.sections[keys[0]]
            order = sample(list(chosenSec.values()), 3)
            chosenPOS = order[0]

            samePOStoStudy = self._getUnstudiedWord(chosenPOS)
            sameSecToStudy = self._getUnstudiedWord(set(order[0] + order[1] + order[2]))
            if len(samePOStoStudy) >= 3:
                chosenWords = sample(samePOStoStudy, 3) #correct answers
            elif len(sameSecToStudy) >= 3:
                chosenWords = sample(sameSecToStudy, 3)
            else:
                continue
            correctAnswer = [word[0] for word in chosenWords]

            incorrect = self._getSimilarWords(chosenSec, correctAnswer)

            if len(incorrect) >= 3 and choice([0,1]) == 0:
                pass
            else:
                incorrect = self._getRandomWords(keys)

            incorrect_choices = sample(incorrect, 3)

            candidates = correctAnswer + [item[0] for item in incorrect_choices]
            shuffle(candidates)

            print("\n请键入选项数字,（如：123）。键入q可退出\n从下列词汇中选择有 “" + keys[0] + "” 意义的词汇：", flush=True)
            for i in range(len(candidates)):
                print(str(i+1) + ". " + candidates[i], end='    ')

            allowed = set([str(i+1) for i in range(len(candidates))])
            userAnswer = None
            while userAnswer == None or not set(userAnswer).issubset(allowed):
                userAnswer = input("\n>>>")
                if userAnswer == 'q':
                    return
            self._evaluate(userAnswer, correctAnswer, candidates)

            print("正确答案：")
            for word in chosenWords:
                print(word[0], word[1], word[2])
            print("\n其他选项：")
            for word in incorrect_choices:
                print(word[0], word[1], word[2])
            print("已经学会了" + str(round(len(self.mastered) / len(self.vocab) * 100, 1)) + "%的词", flush = True)


    def _updateStudyRecord(self, correct, incorrect):
        #if you got it right the first time, add to mastered
        #else remove it from studylist
        for word in correct:
            if word not in self.studylist:
                self.mastered.add(word)
            else:
                self.studylist.remove(word)
        #if you got it wrong, add it to studylist, remove it from mastered
        for word in incorrect:
            self.studylist.add(word)
            if word in self.mastered:
                self.mastered.remove(word)
        #update everytime
        with open("mastered.txt", "w+") as f:
            for word in self.mastered:
                f.write(word + "\n\t")
        with open("studylist.txt", "w+") as f:
            for word in self.studylist:
                f.write(word + "\n\t")






    def _evaluate(self, answer, correctAnswer, candidates):
        answeredWords = set()
        for i in answer:
            answeredWords.add(candidates[int(i)-1])
        correctAnswer = set(correctAnswer)
        gotIt =  answeredWords.intersection(correctAnswer)
        overRecall = answeredWords - correctAnswer
        omitted = correctAnswer - answeredWords
        missed = overRecall | omitted

        if not overRecall and not omitted:
            print("对了")
        else:
            print("不对，请复习这几个单词", end = ' ')
            for word in missed:
                print(word, end = ' ')
            print("\n\t")
        self._updateStudyRecord(gotIt, missed)





def cls():
    os.system("cls" if os.name == "nt" else "clear")

def main():
    game = Game(0, 16) #TODO everytime: put the section range you would like to study
    choice = ""
    while choice != 'q':
        choice = input("欢迎来背单词，按s开始，按q退出，按m查看已掌握的单词，按n查看需加强复习的单词\n>>>")
        if choice == 's':
            cls()
            game.getChoices()
        elif choice == 'm':
            print(game.mastered)
        elif choice == 'n':
            print(game.studylist)



if __name__ == "__main__":
    # execute only if run as a script
    main()
