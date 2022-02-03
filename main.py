#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
import time
import math
import random


# Create your objects here.
ev3 = EV3Brick()
DistanceSensor = UltrasonicSensor(Port.S1)
colorSensor = ColorSensor(Port.S2) 
gyroSensor = GyroSensor(Port.S3)
# TouchSensor_in_4 = TouchSensor(Port.S4)

#Initialise Motors
crane_motor_out_b = Motor(Port.B)
left_motor_out_a = Motor(Port.A, positive_direction=Direction.COUNTERCLOCKWISE)
right_motor_out_c = Motor(Port.C, positive_direction=Direction.COUNTERCLOCKWISE)

#Initialise DriveBase
robot = DriveBase(left_motor_out_a, right_motor_out_c, wheel_diameter=31.2, axle_track=178)
robot.settings(straight_speed = 500, straight_acceleration = 500, turn_rate = 1000, turn_acceleration = 1000)

# Write your program here.


# the key is the round number and the value is
# a list of enemies wich will attack or appear in that round


#initialising

bot = Defender()
soundAttack = bot.SoundAttack()
touchAttack = bot.TouchAttack()
craneAttack = bot.CraneAttack()

bot_attacks = [soundAttack, touchAttack, craneAttack ]

bandage = bot.Bandage()
firstAidKit = bot.FirstAidKit()
medicalKit = bot.MedicalKit()

bot_heals = [bandage, firstAidKit, medicalKit]

# the key is the slot number and the value is enemy in that slot

total_rounds = 13
max_angle = 360
angle_step = 60

enemy_moves = {
    "1": [],
    "2": [],
    "3": [],
    "4": [],
    "5": [],
    "6": [],
}

# Classes

class Defender():

    memory = {
        "1": None,
        "2": None,
        "3": None,
        "4": None,
        "5": None,
        "6": None}

    current_angle = 0
    
    def __init__(self):
        self.name = "Defender Bot"
        self.bot_hp = 750
        self.bot_energy = 500

    def getSortedEnemies(self) :
        sorted_enemies = {}
        impact_attacks = []
        for enemy in self.memory:
            if self.memory[enemy] != None:
                impact_attacks.append(self.memory[enemy].impact_attack)
        impact_attacks.sort(reverse = True)
        if len(impact_attacks) != 0:
            for impact in impact_attacks:
                for slot in self.memory:
                    if self.memory[slot] != None:
                        if self.memory[slot].impact_attack == impact :
                            if self.memory[slot] not in sorted_enemies.values():
                                sorted_enemies[slot] = self.memory[slot]
                                break
        print("Sorted enemies : " + str(sorted_enemies))
        return sorted_enemies

    def getPossibleAttacks(self, attacks) :
        possible_attacks = []
        for attack in attacks:
            if self.bot_energy > attack.consumption :
                possible_attacks.append(attack)
        return possible_attacks

    def getPossibleHeals(self, heals):
        possible_heals = []
        for heal in heals:
            if self.bot_energy > heal.consumption :
                possible_heals.append(heal)
        return possible_heals
    
    def smartMove(self, attacks, heals) :
        sorted_enem = self.getSortedEnemies()
        
        if self.getTakenDamage() >= self.bot_hp and self.bot_hp < 750:
            if len(self.getPossibleHeals(heals)) > 0:
                for heal in self.getPossibleHeals(heals):
                    if self.bot_hp + heal.recovered_life > self.getTakenDamage() :
                        best_heal = heal
                        print("Best heal is : " + str(best_heal))
                        break
                    elif self.bot_hp + heal.recovered_life < self.getTakenDamage():
                        best_heal = self.getPossibleHeals(heals)[0]
                        print("Too big damage in next round - Bot will die anyway so he can use for example : " + str(best_heal))
                print("[BOT] -- Bot healed with " + str(best_heal.name))
                best_heal.do(self)
        else :
            for enemy in sorted_enem :
                for attack in self.getPossibleAttacks(attacks):
                    if sorted_enem[enemy].hp <= attack.damage:
                        ev3.speaker.say("Robot Attack " + sorted_enem[enemy].name + " with " + attack.name)
                        print("[BOT] -- Bot attack " + str(sorted_enem[enemy].name) + " with " + attack.name)
                        attack.do(self, sorted_enem[enemy])
                        break
            robot.turn(360 - bot.current_angle)
            bot.current_angle = 360
        self.memoryManager()

    def getTakenDamage(self) :
        total_damage = 0
        for enemy in self.memory:
            if self.memory[enemy] != None :
                if self.memory[enemy].firstAppearance == False:
                    total_damage += self.memory[enemy].damage
        return total_damage
        
    def memoryManager(self) :
        eliminate_list = []
        for slot in self.memory:
            if self.memory[slot] != None:
                if self.memory[slot].hp <= 0 or self.memory[slot].nr_of_attacks <= 0:
                    eliminate_list.append(slot)
        if len(eliminate_list) != 0:
            for enemy in eliminate_list:
                print(str(self.memory[enemy].name) + " " + str(self.memory[enemy]) + " eliminated!")
                ev3.speaker.say(self.memory[enemy].name + " eliminated")
                self.memory[enemy] = None
        print("Enemies in defender memory: " + str(self.memory))
                    
    def scanEnv(self, environment) :
        enemies = Scan(environment)
        #adauga in sloturile goale la bot.memory - enemies din search
        for enemy in enemies :
            for slot in self.memory :
                if self.memory[slot] == None :
                    self.memory[slot] = enemies[enemy]
                    break

    def recoverEnergy(self):
        if self.bot_energy < 500:
            self.bot_energy += 0.5 * self.bot_energy
            ev3.speaker.play_file(SoundFile.AIR_RELEASE)
            print("Bot recovered half of its current energy")
        if self.bot_energy > 500:
            aux = self.bot_energy - 500
            self.bot_energy -= aux

    def info(self):
        print("_____DEFENDER-BOT_____")
        print("HP : " + str(self.bot_hp))
        print("ENERGY : " + str(self.bot_energy))
        print("______________________")
# clasa de attack
    class Attack():
        name = ''
        damage = 0
        consumption = 0
        sound = None

        def __init__(self, name, damage, consumption, sound):
            self.name = name
            self.damage = damage
            self.consumption = consumption
            self.sound = None

        def do(self, bot, enemy):
            if bot.current_angle != enemy.position :
                robot.turn(enemy.position - bot.current_angle)
                bot.current_angle = enemy.position 
                robot.straight(360)
                self.doAttack()
                enemy.hp -= self.damage
                bot.bot_energy -= self.consumption
                robot.straight(-360)
            else :
                robot.straight(360)
                self.doAttack()
                enemy.hp -= self.damage
                bot.bot_energy -= self.consumption
                robot.straight(-360)
            bot.info()
            self.info()
            enemy.info()

        def info(self):
            print("________ATTACK________")
            print('NAME : ' + self.name)
            print("DAMAGE : " + str(self.damage))
            print("CONSUMPTION : " + str(self.consumption))
            print("______________________")
# aici is attackurile care extind clasa attack

    class CraneAttack(Attack):
        def __init__(self):
            self.name = "Crane Attack"
            self.damage = 200
            self.consumption = 300

        def doAttack(self):
            robot.straight(-30)
            robot.turn(180)
            robot.straight(-30)
            crane_motor_out_b.run_target(1000, 360, then = Stop.HOLD, wait=True )
            robot.straight(30)
            robot.turn(-180)
            robot.straight(30)

    class TouchAttack(Attack):
        def __init__(self):
            self.name = "Touch Attack"
            self.damage = 100
            self.consumption = 150
            self.sound = SoundFile.TOUCH

        def doAttack(self):
            robot.straight(-30)
            robot.turn(180)
            robot.straight(-50)
            ev3.speaker.play_file(self.sound)
            robot.straight(20)
            robot.turn(-180)

    class SoundAttack(Attack):
        def __init__(self):
            self.name = "Sound Attack"
            self.damage = 50
            self.consumption = 50
            self.sound = SoundFile.LASER

        def doAttack(self):
            ev3.speaker.play_file(self.sound)
# asta e lecenia - clasa principala

    class Cure():
        name = ''
        recovered_life = 0
        consumption = 0 
        sound = None
        
        def __init__(self, name, recovered_life, consumption, sound):
            self.name = name
            self.recovered_life = recovered_life
            self.consumption = consumption
            self.sound = sound

        def info(self):
            print("_________CURE_________")
            print('NAME : ' + self.name)
            print("RECOVERED LIFE : " + str(self.recovered_life))
            print("CONSUMPTION : " + str(self.consumption))
            print("______________________")

        def do(self, bot):
            bot.bot_hp += self.recovered_life
            bot.bot_energy -= self.consumption
            ev3.speaker.play_file(self.sound)
            print("Robot healed with " + self.name)
            ev3.speaker.say("Robot healed with " + self.name)
            bot.info()
            self.info()
            
# asta e bandage tipa cea mai slaba aptecika(am luat conceptul si denumirile de la PUBG :D )
    class Bandage(Cure):
        def __init__(self):
            self.name = "Bandage"
            self.recovered_life = 100
            self.consumption = 200
            self.sound = SoundFile.MAGIC_WAND
        
    class FirstAidKit(Cure):
        def __init__(self):
            self.name = "First Aid Kit"
            self.recovered_life = 200
            self.consumption = 300
            self.sound = SoundFile.THANK_YOU

    class MedicalKit(Cure):
        def __init__(self):
            self.name = "Medical Kit"
            self.recovered_life = 400
            self.consumption = 400
            self.sound = SoundFile.YES


class Enemy():
    name = ""
    damage = 0
    nr_of_attacks = 0
    hp = 0
    max_hp = 0
    impact_attack = 0
    position = 0
    firstAppearance = True
    sound = None

    def __init__(self, name,  hp, damage, max_hp, nr_of_attacks, position, sound):
        self.name = name
        self.damage = damage
        self.nr_of_attacks = nr_of_attacks
        self.hp = hp
        self.impact_attack = math.trunc(damage * (hp/max_hp))
        self.position = position
        self.sound = sound

    def info(self):
        print("________ENEMY________")
        print("Name : " + self.name)
        print("HP : " + str(self.hp))
        print("STRENGHT : " + str(self.damage))
        print("NR_OF_ATTACKS : " + str(self.nr_of_attacks))
        print("IMPACT ATTACK : " + str(self.impact_attack))
        print("POSITION : " + str(self.position))
        print("______________________")

    def Attack(self, defender):
        if self.nr_of_attacks > 0:
            defender.bot_hp -= self.damage
            self.nr_of_attacks -= 1
            ev3.speaker.say(self.name + " Attack Robot ")
            ev3.speaker.play_file(self.sound)
        else:
            print(self.name + " can't attack, doesn't have more attacks")
        self.info()
        defender.info()

class Tank(Enemy):
    def __init__(self):
        self.name = "Tank"
        self.damage = 200
        self.nr_of_attacks = 2
        self.hp = 200
        self.max_hp = 200
        self.impact_attack = math.trunc(self.damage * (self.hp/self.max_hp))
        self.sound = "sounds/tank.wav"
# clasul la Artilleria care extinde clasul Enemy

class Artillery(Enemy):
    def __init__(self):
        self.name = "Artillery"
        self.damage = 500
        self.nr_of_attacks = 1
        self.hp = 50
        self.max_hp = 50
        self.impact_attack = math.trunc(self.damage * (self.hp/self.max_hp))
        self.sound = "sounds/art.wav"
# clasul la soldat care extinde clasul Enemy

class Infantry(Enemy):
    def __init__(self):
        self.name = "Infantry"
        self.damage = 100
        self.nr_of_attacks = 3
        self.hp = 100
        self.max_hp = 100
        self.impact_attack = math.trunc(self.damage * (self.hp/self.max_hp))
        self.sound = "sounds/inf.wav"

# asta prosta genereaza numerele - il folosesc in GenerateMoves

def ThrowDices():
    firstDice = random.randint(1, 6)
    secondDice = random.randint(1, 6)

    if secondDice == 1 or secondDice == 2:
        secondDice = Tank()
    elif secondDice == 3 or secondDice == 4:
        secondDice = Artillery()
    elif secondDice == 5 or secondDice == 6:
        secondDice = Infantry()

    dices = [firstDice, secondDice]

    return dices

# asta genereaza tabela ceia unde primul zar - e in ce round apare si al doilea zar e cine apare

def GenerateMoves():
    global enemy_moves

    for i in range(1, 7):
        dices = ThrowDices()
        enemy_moves.setdefault(str(dices[0]), []).append(dices[1])
    
    # enemy_moves.setdefault("1", []).append(Tank())
    # enemy_moves.setdefault("1", []).append(Tank())
    # enemy_moves.setdefault("4", []).append(Artillery())
    # enemy_moves.setdefault("4", []).append(Infantry())
    # enemy_moves.setdefault("6", []).append(Tank())
    # enemy_moves.setdefault("6", []).append(Infantry())
    
# asta afiseaza in ce round ce enemy trebuie sa apara

def ShowMoves():
    for round in enemy_moves:
        print("In the round " + round)
        if len(enemy_moves[round]) == 0:
            print("\tNone")
        else:
            for enemy in enemy_moves[round]:
                print("\t" + enemy.name)
        print('\n')

# aici controlez daca e par sau impar numarul ca sa vad a cui e randul

def wichTurn(round):
    if round % 2 == 0:
        return "bot"
    else:
        return "enemy"

def Game():
    GenerateMoves()

    # Bot/attacks/heals initialisation

    #initialising nr of rounds and environment
    env = []
    enemy_round = 1
    defender_round = 0
    current_round = enemy_round + defender_round

    def SayWichRound() :
        if current_round == 1 :
            return "1"
        elif current_round == 2 :
            return "2"
        elif current_round == 3 :
            return "3"
        elif current_round == 4 :
            return "4"
        elif current_round == 5 :
            return "5"
        elif current_round == 6 :
            return "6"
        elif current_round == 7 :
            return "7"
        elif current_round == 8 :
            return "8"
        elif current_round == 9 :
            return "9"
        elif current_round == 10 :
            return "10"
        elif current_round == 11 :
            return "11"
        elif current_round == 12 :
            return "12"
        elif current_round == 13 :
            return "13"

    def CheckForWin() :
        if bot.bot_hp <= 0 :
            print("############ GAME OVER ############")
            ev3.speaker.play_file(SoundFile.GAME_OVER)
        elif current_round == 13 and bot.bot_hp > 0 :
            print("############ DEFENDER BOT WON ############")
            ev3.speaker.play_file("sounds/victory.wav")
    
    # here is the main counter of the game
    while current_round <= total_rounds:
        print("_______________________________ROUND " + str(current_round) +  "_______________________________")
        ev3.speaker.say("Round " + SayWichRound())
        #check if it's enemy tur
        
        if wichTurn(current_round) == "enemy":
            if enemy_round == 7 :
                print("Enemy round : " + str(enemy_round))
                for enemy in bot.memory:
                    if bot.memory[enemy] != None :
                        if bot.memory[enemy].firstAppearance == False:
                            print("[ENEMY] -- " + bot.memory[enemy].name + " attacked Bot")
                            bot.memory[enemy].Attack(bot)
                    CheckForWin()
                print("No enemies appearing in " + str(current_round) + " round")    
                enemy_round += 1
                current_round = enemy_round + defender_round
            else :
                # ----------------------------------- #
                #checking if array from current enemy_round is empty / if in that round exists some enemies to appear
                if len(enemy_moves[str(enemy_round)]) == 0:
                    print("Enemy round : " + str(enemy_round))
                    for enemy in bot.memory:
                        if bot.memory[enemy] != None :
                            if bot.memory[enemy].firstAppearance == False:
                                print("[ENEMY] -- " + bot.memory[enemy].name + " attacked Bot")
                                bot.memory[enemy].Attack(bot)
                        CheckForWin()
                    print("No enemies appearing in " + str(current_round) + " round")    
                    enemy_round += 1
                    current_round = enemy_round + defender_round

                
                #if in that array exists enemies then we append those enemies in the environment
                else:
                    print("Enemy round : " + str(enemy_round))
                    for enemy in enemy_moves[str(enemy_round)]:
                        env.append(enemy)
                    for enemy in bot.memory:
                        if bot.memory[enemy] != None: 
                            if bot.memory[enemy].firstAppearance == False:
                                bot.memory[enemy].Attack(bot)
                                print("[ENEMY] -- " + bot.memory[enemy].name + " attacked Bot")
                        CheckForWin()
                    print("In round " + str(current_round) + " added : ")
                    print(env)
                    enemy_round += 1
                    current_round = enemy_round + defender_round


        #If it's the robot turn
        else:
            defender_round += 1
            print("Defender round : " + str(defender_round))
            bot.recoverEnergy()
            bot.scanEnv(env)
            bot.smartMove(bot_attacks, bot_heals)
            
            for slot in bot.memory :
                if bot.memory[slot] != None:
                    bot.memory[slot].firstAppearance = False
            env = []
            
            current_round = enemy_round + defender_round
            
        ev3.speaker.beep()
        
        print("PRESS CENTER BUTTON TO CONTINUE")
        while True:
            pressed = Button.CENTER in ev3.buttons.pressed()
            if pressed == True:
                time.sleep(2)
                break

def Scan(environment):
    index = 0

    enemies = {
        "1" : None,
        "2" : None,
        "3" : None,
        "4" : None,
        "5" : None,
        "6" : None,}
    
    def memorise(enemy, environment) :
        enemies[str(index)] = enemy
        if angle == 0 or angle == 360 :
            enemies[str(index)].position = 360
        else :
            enemies[str(index)].position = angle
        environment.remove(enemy)
        print(str(enemies[str(index)].name) + " found at slot " + str(math.trunc((angle/60)+1)) + " ANGLE = " + str(enemies[str(index)].position))
    
    def CheckColor() :
        for enemy in environment:
            if (colorSensor.color() == Color.YELLOW or colorSensor.color() == Color.BROWN) and enemy.name == "Tank":
                memorise(enemy, environment)
                ev3.speaker.say(enemy.name)
                break
            elif colorSensor.color() == Color.RED and enemy.name == "Artillery":
                memorise(enemy, environment)
                ev3.speaker.say(enemy.name)
                break
            elif (colorSensor.color() == Color.GREEN or colorSensor.color() == Color.BLUE) and enemy.name == "Infantry":
                memorise(enemy, environment)
                ev3.speaker.say(enemy.name)
                break

    ev3.speaker.say("Analyze")
    for angle in range(0, max_angle, angle_step):
        index += 1
        if DistanceSensor.distance() < 500 : 
            ev3.speaker.say("Detected")
            robot.straight(370)
            if colorSensor.color() != Color.BLACK and colorSensor.color() != None :
                CheckColor()
            else : 
                while colorSensor.color() == Color.BLACK or colorSensor.color() == None :
                    robot.straight(-30)
                    robot.straight(30)
                CheckColor()
            robot.straight(-370)
        
        robot.turn(angle_step)

        if angle == 0:
            bot.current_angle = 360
        else :
            bot.current_angle = angle

    bot.current_angle = 360
    return enemies
    

if __name__ == "__main__" :
    ev3.speaker.beep()
    Game()
