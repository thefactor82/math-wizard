import pygame 
import random 
import sys 
import os 
import json 
import re 
import math 
from datetime import datetime 
from collections import deque 
from fractions import Fraction 

def resource_path (relative ):
    return os .path .join (getattr (sys ,'_MEIPASS',os .path .dirname (os .path .abspath (__file__ ))),relative )

def data_path (relative ):
    base =os .path .dirname (sys .executable )if getattr (sys ,'frozen',False )else os .path .dirname (os .path .abspath (__file__ ))
    return os .path .join (base ,relative )

PROFILES_DIR ="profiles"

WIZARD_LIVES =3 
DEFAULT_TIMEOUT =12 
SCREEN_WIDTH =1280 
SCREEN_HEIGHT =720 
FPS =60 

WHITE =(255 ,255 ,255 )
BLACK =(0 ,0 ,0 )
RED =(220 ,50 ,50 )
GREEN =(50 ,220 ,50 )
YELLOW =(255 ,255 ,0 )
GOLD =(255 ,215 ,0 )
GRAY =(100 ,100 ,100 )
DARK =(20 ,20 ,30 )
BG_DARK =(30 ,30 ,50 )
SEL_BLUE =(60 ,130 ,200 )

def parse_pool (val ):
    if isinstance (val ,list ):
        return val 
    if isinstance (val ,str ):
        result =[]
        for part in val .split (","):
            part =part .strip ()
            if "-"in part :
                a ,b =part .split ("-",1 )
                result .extend (range (int (a ),int (b )+1 ))
            else :
                result .append (int (part ))
        return result 
    return val 

def sanitize_profile_name (name ):
    if not isinstance (name ,str ):
        return None 
    name =name .strip ()
    if not name or name in (".",".."):
        return None 
    if "/"in name or "\\"in name :
        return None 
    return name if re .match (r"^[A-Za-z0-9_-]+$",name )else None 

def make_placeholder_surface (size ,color =(80 ,80 ,90 )):
    surf =pygame .Surface (size ,pygame .SRCALPHA )
    surf .fill (color )
    return surf 

def safe_load_image (path ,scale =None ,convert_alpha =True ):
    try :
        img =pygame .image .load (path )
        if convert_alpha :
            img =img .convert_alpha ()
        else :
            img =img .convert ()
        if scale is not None :
            img =pygame .transform .scale (img ,scale )
        return img 
    except (pygame .error ,OSError )as e :
        print (f"Warning: unable to load image '{path }': {e }")
        return make_placeholder_surface (scale if scale is not None else (100 ,100 ))


def load_json_file (path ):
    try :
        with open (path ,"r",encoding ="utf-8")as f :
            return json .load (f )
    except (OSError ,json .JSONDecodeError )as e :
        print (f"Warning: unable to load JSON '{path }': {e }")
        return None 


def save_json_file (path ,data ):
    try :
        dir_name =os .path .dirname (path )
        if dir_name :
            os .makedirs (dir_name ,exist_ok =True )
        with open (path ,"w",encoding ="utf-8")as f :
            json .dump (data ,f ,indent =2 )
    except OSError as e :
        print (f"Warning: unable to save JSON '{path }': {e }")


def normalize_pool_list (raw_pool ,length ):
    if isinstance (raw_pool ,str ):
        raw_pool =parse_pool (raw_pool )
    if isinstance (raw_pool ,list ):
        if all (isinstance (x ,bool )for x in raw_pool ):
            result =[bool (x )for x in raw_pool [:length ]]
            result +=[False ]*max (0 ,length -len (result ))
            return result 
        if all (isinstance (x ,int )for x in raw_pool ):
            pool =[False ]*length 
            for n in raw_pool :
                if 0 <=n <length :
                    pool [n ]=True 
            return pool 
    return [False ]*length 


def format_pool_compact (nums ):
    if not nums :
        return "[]"
    if all (isinstance (x ,int )for x in nums ):
        nums =sorted (set (nums ))
        parts =[]
        start =nums [0]
        end =nums [0]
        for n in nums [1:]:
            if n ==end +1 :
                end =n 
            else :
                parts .append (f"{start }-{end }"if start !=end else str (start ))
                start =end =n 
        parts .append (f"{start }-{end }"if start !=end else str (start ))
        return ",".join (parts )
    return str (nums )


def get_operation_symbol (operation ):
    if operation =="sottrazione":
        return "-"
    if operation =="addizione":
        return "+"
    if operation =="divisione":
        return ":"
    return "x"


def calculate_result (a ,b ,operation ,integer_result =True ):
    if operation =="addizione":
        return a +b 
    if operation =="sottrazione":
        return a -b 
    if operation =="divisione":
        if b ==0 :
            return 0 
        return a //b if integer_result else a /b 
    return a *b 


def finite_decimal_places (a ,b ,max_places =2 ):
    if b ==0 :
        return None 
    frac =Fraction (a ,b )
    if frac .denominator ==1 :
        return 0 
    denom =frac .denominator 
    while denom %2 ==0 :
        denom //=2 
    while denom %5 ==0 :
        denom //=5 
    if denom !=1 :
        return None 
    for places in range (1 ,max_places +1 ):
        if (frac *10 **places ).denominator ==1 :
            return places 
    return None 


def is_answer_correct (risposta ,atteso ):
    if isinstance (atteso ,float )or isinstance (risposta ,float ):
        return abs (risposta -atteso )<1e-6 
    return risposta ==atteso 


def generate_addition_operands (pool_a ,pool_b ,reinforce_queue ,max_sum =None ):
    if reinforce_queue and random .random ()<0.4 :
        return reinforce_queue .popleft ()
    a =random .choice (pool_a )
    b =random .choice (pool_b )
    if max_sum is None :
        return a ,b 
    for _ in range (50 ):
        if a +b <=max_sum :
            return a ,b 
        a =random .choice (pool_a )
        b =random .choice (pool_b )
    fallback_b =0 if 0 in pool_b else random .choice (pool_b )
    return min (pool_a ,key =lambda x :abs (x -max_sum )),fallback_b 


def select_operands (pool_a ,pool_b ,reinforce_queue ,operation ,integer_result =True ,max_sum =None ):
    if operation =="divisione":
        return generate_division_operands (pool_a ,pool_b ,reinforce_queue ,integer_result )
    if operation =="addizione":
        return generate_addition_operands (pool_a ,pool_b ,reinforce_queue ,max_sum )
    return generate_operands (pool_a ,pool_b ,reinforce_queue )

LEVELS ={}
for src in (data_path ,resource_path ):
    levels_path =src ("data/levels.json")
    if os .path .exists (levels_path ):
        data =load_json_file (levels_path )
        if isinstance (data ,dict ):
            LEVELS =data 
            for op in LEVELS :
                for lv in LEVELS [op ]:
                    lv ["pool_a"]=parse_pool (lv ["pool_a"])
                    lv ["pool_b"]=parse_pool (lv ["pool_b"])
        if LEVELS :
            break 
if not LEVELS :
    LEVELS ={"moltiplicazione":[],"addizione":[],"sottrazione":[],"divisione":[]}
default_level ={"pool_a":[0 ,1 ,2 ,3 ,4 ,5 ,6 ,7 ,8 ,9 ],"pool_b":[0 ,1 ,2 ,3 ,4 ,5 ,6 ,7 ,8 ,9 ]}
for op in ["moltiplicazione","addizione","sottrazione","divisione"]:
    if op not in LEVELS or not LEVELS [op ]:
        LEVELS [op ]=[default_level ]

NUMPAD_DIGIT ={
pygame .K_KP0 :0 ,pygame .K_KP_0 :0 ,
pygame .K_KP1 :1 ,pygame .K_KP_1 :1 ,
pygame .K_KP2 :2 ,pygame .K_KP_2 :2 ,
pygame .K_KP3 :3 ,pygame .K_KP_3 :3 ,
pygame .K_KP4 :4 ,pygame .K_KP_4 :4 ,
pygame .K_KP5 :5 ,pygame .K_KP_5 :5 ,
pygame .K_KP6 :6 ,pygame .K_KP_6 :6 ,
pygame .K_KP7 :7 ,pygame .K_KP_7 :7 ,
pygame .K_KP8 :8 ,pygame .K_KP_8 :8 ,
pygame .K_KP9 :9 ,pygame .K_KP_9 :9 ,
}

def generate_operands (pool_a ,pool_b ,reinforce_queue ):
    if reinforce_queue and random .random ()<0.4 :
        return reinforce_queue .popleft ()
    return random .choice (pool_a ),random .choice (pool_b )

def generate_division_operands (pool_a ,pool_b ,reinforce_queue ,integer_result =True ):
    valid_b =[b for b in pool_b if b !=0 ]
    if not valid_b :
        return 1 ,1 
    if integer_result :
        while reinforce_queue :
            a ,b =reinforce_queue .popleft ()
            if b !=0 and a >0 and a %b ==0 :
                return a ,b 
        for _ in range (50 ):
            b =random .choice (valid_b )
            valid_a =[a for a in pool_a if a >0 and a %b ==0 ]
            if valid_a :
                return random .choice (valid_a ),b 
        b =random .choice (valid_b )
        return b ,b 

    while reinforce_queue :
        a ,b =reinforce_queue .popleft ()
        if b !=0 and finite_decimal_places (a ,b )is not None :
            return a ,b 

    for _ in range (100 ):
        b =random .choice (valid_b )
        a =random .choice (pool_a )
        if finite_decimal_places (a ,b )is not None :
            if a %b !=0 or pool_b .count (b )==1 :
                return a ,b 
    for _ in range (50 ):
        b =random .choice (valid_b )
        a =random .choice (pool_a )
        if finite_decimal_places (a ,b )is not None :
            return a ,b 
    return random .choice (pool_a ),random .choice (valid_b )

class Game :
    def __init__ (self ):
        pygame .init ()
        self .fullscreen =False 
        self .flags =pygame .SCALED 
        self .screen =pygame .display .set_mode ((SCREEN_WIDTH ,SCREEN_HEIGHT ),self .flags )
        pygame .display .set_caption ("Math Wizard - Impara la matematica")
        self .setup_cursor ()
        self .clock =pygame .time .Clock ()
        self .running =True 
        self .state ="splash"
        self .splash_start =pygame .time .get_ticks ()
        self .splash_skip =False 
        self .player_exit_retry =False 
        self .return_to_game =False 
        self .character_entry =False 
        self .character_entry_start =0 
        self .character_entry_x =0 
        self .player_in_dir ="sx"
        self .player_out_dir ="dx"
        self .player_entrance =True 
        self .monster_in_dir ="dx"
        self .player_flip =False 
        self .player_stand_x =75 
        self .monster_type ="walk"
        self .monster_y_offset =0 
        self .debug =False 
        self .debug_buf =""

        self .font_title =pygame .font .Font (None ,80 )
        self .font_large =pygame .font .Font (None ,64 )
        self .font_medium =pygame .font .Font (None ,42 )
        self .story_font =pygame .font .Font (None ,48 )
        self .font_small =pygame .font .Font (None ,30 )
        self .font_input =pygame .font .Font (None ,56 )
        self .font_stats =pygame .font .Font (None ,28 )
        self .font_num =pygame .font .Font (None ,36 )
        self .font_tiny =pygame .font .Font (None ,22 )

        self .load_resources ()
        self .setup_profiles ()
        self .reset_game_state ()

    def setup_cursor (self ):
        try :
            import struct ,io ,os 
            path =resource_path (os .path .join ("graphics","misc","wand.cur"))
            if not os .path .exists (path ):
                return 
            with open (path ,"rb")as f :
                data =f .read ()
            _ ,_ ,count =struct .unpack ("<HHH",data [:6 ])
            # Pick the best entry: prefer 32x32, fallback to largest
            best =None 
            for i in range (count ):
                w ,h ,_ ,_ ,_ ,_ ,sz ,off =struct .unpack ("<BBBBHHII",data [6 +i *16 :22 +i *16 ])
                if w ==32 :
                    best =(off ,sz ,w ,h )
                    break 
                if best is None or w >best [2 ]:
                    best =(off ,sz ,w ,h )
            if best is None :
                return 
            off ,sz ,w ,h =best 
            buf =io .BytesIO (data [off :off +sz ])
            surf =pygame .image .load (buf )
            if not (surf .get_flags ()&pygame .SRCALPHA ):
                surf =surf .convert_alpha ()
            surf =pygame .transform .scale_by (surf ,3 )
            cursor =pygame .cursors .Cursor ((0 ,0 ),surf )
            pygame .mouse .set_cursor (cursor )
        except (OSError ,struct .error ,pygame .error )as e :
            print (f"Warning: unable to set custom cursor from wand.cur: {e }")
            return 

    def update_char_image (self ):
        data =self .char_data .get (self .config_gender ,self .char_data ["F"])
        self .char_img =data ["idle"][0 ]
        self .char_w ,self .char_h =self .char_img .get_size ()

    def load_resources (self ):
        self .bg =safe_load_image (resource_path ("graphics/backgrounds/background1.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))
        self .bg_menu =safe_load_image (resource_path ("graphics/MISC/background_menu.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))
        self .bg_options =safe_load_image (resource_path ("graphics/MISC/background_options.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))

        self .backgrounds ={}
        bg_dir =resource_path ("graphics/backgrounds")
        if os .path .isdir (bg_dir ):
            for fname in sorted (os .listdir (bg_dir )):
                if fname .lower ().endswith ((".png",".jpg",".bmp")):
                    stem =os .path .splitext (fname )[0 ]
                    img =safe_load_image (os .path .join (bg_dir ,fname ),(SCREEN_WIDTH ,SCREEN_HEIGHT ))
                    self .backgrounds [stem ]=img 
        self .backgrounds ["game"]=self .bg 
        self .backgrounds ["menu"]=self .bg_menu 
        self .backgrounds ["options"]=self .bg_options 
        self .game_bg =self .bg 

        pw ,ph =900 ,1330 
        target_w =160 
        self .char_data ={}
        for key ,path in [("F",resource_path ("graphics/players/playerf.png")),("M",resource_path ("graphics/players/playerm.png"))]:
            idle_frames =self .load_spritesheet (path ,160 ,2 ,row =1 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False )
            profile_img =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False )[0 ]
            hit_frame =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =3 ,flip_x =False ,scale =False )[0 ]
            charge_frame =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =2 ,flip_x =False ,scale =False )[0 ]
            self .char_data [key ]={"idle":idle_frames ,"profile":profile_img ,"hit":hit_frame ,"charge":charge_frame }
            run_frames =self .load_spritesheet (path ,160 ,4 ,row =0 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False )
            self .char_data [key ]["run"]=run_frames 
        self .char_img =self .char_data ["F"]["idle"][0 ]
        self .char_h =self .char_img .get_height ()
        self .char_anim_timer =0 
        self .char_anim_frame =0 

        self .monsters =[]
        monster_dir =resource_path ("graphics/monsters")
        if os .path .isdir (monster_dir ):
            for fname in sorted (os .listdir (monster_dir )):
                if fname .lower ().startswith ("monster")and fname .lower ().endswith (".png"):
                    try :
                        mi =int (fname .replace ("monster","").replace (".png","").replace ("M",""))
                    except ValueError :
                        continue 
                    if mi ==99 :
                        continue 
                    path =os .path .join (monster_dir ,fname )
                    frames =self .load_spritesheet (path ,200 ,4 ,row =0 ,rows =2 ,cols =4 )
                    hit =self .load_spritesheet (path ,200 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =3 )[0 ]
                    self .monsters .append ({"frames":frames ,"hit":hit ,"idx":mi })
        if not self .monsters :
            placeholder_frame =make_placeholder_surface ((200 ,200 ))
            self .monsters .append ({"frames":[placeholder_frame ],"hit":placeholder_frame ,"idx":1 })
        self .monster_frames =self .monsters [0 ]["frames"]
        self .monster_hit_img =self .monsters [0 ]["hit"]
        self .monster_img =self .monster_frames [0 ]
        self .monster_anim_speed =150 
        self .monster_hit_delay =150 
        self .previous_monster =None 

        self .boss_data =None 
        boss_path =resource_path ("graphics/monsters/monster99.png")
        if os .path .exists (boss_path ):
            boss_walk =self .load_spritesheet (boss_path ,390 ,2 ,row =0 ,rows =2 ,cols =2 ,frame_offset =0 ,flip_x =False )
            boss_hit =self .load_spritesheet (boss_path ,390 ,1 ,row =1 ,rows =2 ,cols =2 ,frame_offset =0 ,flip_x =False )[0 ]
            boss_defeated =self .load_spritesheet (boss_path ,390 ,1 ,row =1 ,rows =2 ,cols =2 ,frame_offset =1 ,flip_x =False )[0 ]
            self .boss_data ={"walk":boss_walk ,"hit":boss_hit ,"defeated":boss_defeated }

        self .heart_red =safe_load_image (resource_path ("graphics/misc/lives.png"),(35 ,35 ))
        self .heart_grey =safe_load_image (resource_path ("graphics/misc/lives_lost.png"),(35 ,35 ))

        self .logo =safe_load_image (resource_path ("graphics/misc/logo.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))
        self .gear_img =safe_load_image (resource_path ("graphics/misc/gear.png"),None )

    def load_spritesheet (self ,path ,target_w ,frame_count ,row =0 ,rows =1 ,cols =None ,frame_offset =0 ,flip_x =True ,scale =True ):
        try :
            sheet =pygame .image .load (path ).convert_alpha ()
        except (pygame .error ,OSError )as e :
            print (f"Warning: unable to load sprite sheet '{path }': {e }")
            placeholder =make_placeholder_surface ((target_w ,target_w ))
            return [placeholder ]*frame_count 
        if flip_x :
            sheet =pygame .transform .flip (sheet ,True ,False )
        ncols =cols if cols is not None else frame_count 
        fw =sheet .get_width ()//ncols 
        fh =sheet .get_height ()//rows 
        if fw <=0 or fh <=0 :
            placeholder =make_placeholder_surface ((target_w ,target_w ))
            return [placeholder ]*frame_count 
        frames =[]
        for i in range (frame_count ):
            frame =sheet .subsurface (((i +frame_offset )*fw ,row *fh ,fw ,fh ))
            if scale :
                frames .append (pygame .transform .scale (frame ,(target_w ,int (target_w /fw *fh ))))
            else :
                frames .append (frame )
        return frames 

    def setup_profiles (self ):
        os .makedirs (PROFILES_DIR ,exist_ok =True )
        idx_file =os .path .join (PROFILES_DIR ,"profiles.json")
        self .profile_cursor =0 
        self .profile_input =""
        self .profile_input_mode =False 
        self .profile_gender_mode =False 
        self .new_profile_name =""
        self .config_gender ="F"
        self .config_story_operation ="moltiplicazione"
        self .config_operation ="moltiplicazione"
        self .config_cursor_row =0 
        self .config_cursor_col =0 
        self .config_cursor_subrow =0 
        self .config_by_operation ={}
        for op in ["moltiplicazione","addizione","sottrazione","divisione"]:
            self .config_by_operation [op ]={
            "pool_a":[n <10 for n in range (100 )],
            "pool_b":[n <10 for n in range (100 )],
            "domande":10 ,
            "swap":True ,
            "timeout":DEFAULT_TIMEOUT ,
            }
        self .config_by_operation ["addizione"]["somma_massima"]=10 
        self .config_by_operation ["sottrazione"]["differenza_positiva"]=True 
        self .config_by_operation ["divisione"]["risultato_intero"]=True 
        self .config_by_operation ["divisione"]["swap"]=False 
        self .config =self .config_by_operation [self .config_operation ]
        self .auto_timeout =DEFAULT_TIMEOUT 
        self .initial_level =0 
        self .story_progress ={"moltiplicazione":0 ,"addizione":0 ,"sottrazione":0 ,"divisione":0 }

        self .story_entries =[]
        for src in (data_path ,resource_path ):
            story_path =src ("data/story.json")
            if os .path .exists (story_path ):
                data =load_json_file (story_path )
                if isinstance (data ,list ):
                    self .story_entries =data 
                if self .story_entries :
                    break 
        self .story_idx =0 
        self .num_story_levels =sum (1 for e in self .story_entries if e .get ("tipo")=="livello")

        self .version ="0.8.009"

        self .profiles =[]
        self .current_profile =""
        data =load_json_file (idx_file )
        if isinstance (data ,dict ):
            profiles =[]
            for p in data .get ("profiles",[]):
                p =sanitize_profile_name (p )
                if p and os .path .isdir (os .path .join (PROFILES_DIR ,p )):
                    profiles .append (p )
            self .profiles =list (dict .fromkeys (profiles ))
            current =sanitize_profile_name (data .get ("current",""))
            self .current_profile =current if current in self .profiles else ""
        if self .current_profile in self .profiles :
            self .load_profile_config (self .current_profile )
            self .update_char_image ()

    def save_profiles (self ):
        path =os .path .join (PROFILES_DIR ,"profiles.json")
        save_json_file (path ,{"profiles":self .profiles ,"current":self .current_profile })

    def save_profile_config (self ,nome =None ):
        nome =nome or self .current_profile 
        nome =sanitize_profile_name (nome )
        if not nome :
            return 
        prof_dir =os .path .join (PROFILES_DIR ,nome )
        os .makedirs (prof_dir ,exist_ok =True )
        path =os .path .join (prof_dir ,"config.json")
        data ={
        "genere":self .config_gender ,
        "storia_operazione":self .config_story_operation ,
        "auto_timeout":self .auto_timeout ,
        "livello_iniziale":self .initial_level ,
        "storia_progresso":self .story_progress ,
        }
        for op in ["moltiplicazione","addizione","sottrazione","divisione"]:
            data [op ]=dict (self .config_by_operation [op ])
        save_json_file (path ,data )

    def load_profile_config (self ,nome ):
        nome =sanitize_profile_name (nome )
        if not nome :
            return 
        path =os .path .join (PROFILES_DIR ,nome ,"config.json")
        if not os .path .exists (path ):
            return 
        data =load_json_file (path )
        if not isinstance (data ,dict ):
            return 
        if "moltiplicazione"in data and isinstance (data ["moltiplicazione"],dict ):
            for op in ["moltiplicazione","addizione","sottrazione","divisione"]:
                if op in data and isinstance (data [op ],dict ):
                    if "pool_a"in data [op ]:
                        self .config_by_operation [op ]["pool_a"]=normalize_pool_list (data [op ]["pool_a"],100 )
                    if "pool_b"in data [op ]:
                        self .config_by_operation [op ]["pool_b"]=normalize_pool_list (data [op ]["pool_b"],100 )
                    self .config_by_operation [op ].update ({k :v for k ,v in data [op ].items ()if k not in ("pool_a","pool_b")})
            self .config_gender =data .get ("genere",self .config_gender )
            self .config_story_operation =data .get ("storia_operazione",self .config_story_operation )
            self .auto_timeout =data .get ("auto_timeout",self .auto_timeout )
            self .initial_level =data .get ("livello_iniziale",self .initial_level )
            story_progress =data .get ("storia_progresso",self .story_progress )
            if isinstance (story_progress ,dict ):
                self .story_progress .update (story_progress )
        else :
        # Legacy format
            self .config_gender =data .get ("genere",self .config_gender )
            self .auto_timeout =data .get ("timeout",self .auto_timeout )
            for op in self .config_by_operation :
                self .config_by_operation [op ]["pool_a"]=normalize_pool_list (data .get ("pool_a",self .config_by_operation [op ]["pool_a"]),100 )
                self .config_by_operation [op ]["pool_b"]=normalize_pool_list (data .get ("pool_b",self .config_by_operation [op ]["pool_b"]),100 )
                self .config_by_operation [op ]["domande"]=data .get ("domande",self .config_by_operation [op ]["domande"])
                self .config_by_operation [op ]["swap"]=data .get ("swap",self .config_by_operation [op ]["swap"])
                self .config_by_operation [op ]["timeout"]=data .get ("timeout",self .config_by_operation [op ]["timeout"])
            self .config_by_operation ["addizione"]["somma_massima"]=data .get ("somma_massima",self .config_by_operation ["addizione"]["somma_massima"])
            self .config_by_operation ["sottrazione"]["differenza_positiva"]=data .get ("differenza_positiva",self .config_by_operation ["sottrazione"]["differenza_positiva"])
            self .config_by_operation ["divisione"]["risultato_intero"]=data .get ("risultato_intero",self .config_by_operation ["divisione"]["risultato_intero"])
        self .config =self .config_by_operation [self .config_operation ]

    def sessions_path (self ):
        nome =sanitize_profile_name (self .current_profile )or ".fallback"
        prof_dir =os .path .join (PROFILES_DIR ,nome )
        os .makedirs (prof_dir ,exist_ok =True )
        return os .path .join (prof_dir ,"sessions.txt")

    def reset_game_state (self ):
        self .mode ="auto"
        self .pool_a =list (range (0 ,10 ))
        self .pool_b =list (range (0 ,10 ))
        self .total_questions =10 
        self .questions_asked =0 
        self .lives =WIZARD_LIVES 
        self .level =0 
        self .is_correct =0 
        self .a =0 
        self .b =0 
        self .prev_a =-1 
        self .prev_b =-1 
        self .expected_result =0 
        self .input_utente =""
        self .monster_progress =0.0 
        self .monster_x =SCREEN_WIDTH +30 
        self .monster_hit =False 
        self .monster_fade_start =0 
        self .monster_anim_frame =0 
        self .hit_timer =0 
        self .question_active =False 
        self .feedback =None 
        self .feedback_timer =0 
        self .zap_timer =0 
        self .zap_reverse =False 
        self .player_hit =False 
        self .game_over =False 
        self .question_start =0 
        self .timeout_handled =False 
        self .consecutive_correct =0 
        self .heart_reward_active =False 
        self .heart_reward_start =0 

        self .boss_active =False 
        self .boss_phase =None 
        self .boss_x =0.0 
        self .boss_start_x =0.0 
        self .boss_end_x =0.0 
        self .boss_y =0 
        self .boss_progress =0.0 
        self .boss_questions_asked =0 
        self .boss_total_questions =10 
        self .boss_timeout =60 
        self .boss_frames =[]
        self .boss_hit_img =None 
        self .boss_defeated_img =None 
        self .boss_hit =False 
        self .boss_fade_start =0 
        self .boss_in_dir ="dx"
        self .boss_flip =False 
        self .boss_anim_frame =0 
        self .boss_anim_speed =1000 
        self .boss_hit_start =0 
        self .boss_defeated_start =0 
        self .boss_defeated_timer =0 
        self .boss_entrance_start =0 
        self .boss_shake_start =0 
        self .boss_paused_ms =0 
        self .boss_pause_start =0 

        self .menu_cursor =0 
        self .options_cursor =0 

        self .config_cursor_row =0 
        self .config_cursor_col =0 
        self .config_cursor_subrow =0 

        self .answer_times =[]
        self .monster_times =[]
        self .boss_times =[]
        self .current_block =[]
        self .reinforcement_queue =deque ()
        self .stats ={}

    def show_config (self ):
        self .state ="config_fixed"
        self .config =self .config_by_operation [self .config_operation ]
        self .config_cursor_row =0 
        self .config_cursor_col =0 
        self .config_cursor_subrow =0 

    def start_game (self ):
        self .state ="game"
        self .game_over =False 
        self .lives =WIZARD_LIVES 
        self .timeout_limit =self .auto_timeout if self .mode =="auto"else self .config ["timeout"]
        if self .mode =="auto":
            self .initial_timeout_limit =self .auto_timeout 
            self .levels =LEVELS [self .config_story_operation ]
            self .level =self .initial_level 
        self .story_idx =0 
        self .story_is_level =False 
        self .story_monsters =list (range (1 ,9 ))
        self .story_flying_monsters =[]
        self .story_fade_speed =8 
        self .story_next_bg =None 
        self .story_fade_alpha =0 
        self .story_phase ="show"
        self .story_fade_color =(0 ,0 ,0 )
        self .story_first_step =True 
        self .consecutive_correct =0 
        self .heart_reward_active =False 
        self .heart_reward_start =0 
        self .answer_times =[]
        self .monster_times =[]
        self .boss_times =[]
        self .current_block =[]
        self .reinforcement_queue =deque ()
        self .stats ={}
        self .questions_asked =0 
        self .question_active =False 
        self .feedback =None 
        self .wait_for_enter =False 
        self .prev_a =-1 
        self .prev_b =-1 
        self .game_over =False 
        if self .mode =="fixed":
            bg_keys =[k for k in self .backgrounds if k not in ("menu","options","game")]
            self .game_bg =self .backgrounds [random .choice (bg_keys )]if bg_keys else self .bg 
            self .player_in_dir ="sx"
            self .player_out_dir ="dx"
            self .player_entrance =True 
            self .monster_in_dir ="dx"
            self .player_flip =False 
            self .player_stand_x =75 
            self .operation =self .config_operation 
            self .max_sum =self .config .get ("somma_massima",10 )
            self .positive_difference =self .config .get ("differenza_positiva",True )
            self .integer_result =self .config .get ("risultato_intero",True )
            division =self .config_operation =="divisione"
            pool_range =range (13 )if self .config_operation =="moltiplicazione"else range (100 )
            self .pool_a =[n for n in pool_range if self .config ["pool_a"][n ]]
            self .pool_b =[n for n in pool_range if self .config ["pool_b"][n ]]
            if not self .pool_a :
                self .pool_a =[0 ]
            if not self .pool_b :
                self .pool_b =[0 ]
            self .total_questions =self .config ["domande"]
            self .swap_operandi =True if self .operation =="sottrazione"else self .config ["swap"]
        if self .mode =="auto"and self .story_entries :
            op_cfg =self .config_by_operation .get (self .config_story_operation ,{})
            self .operation =self .config_story_operation 
            self .config =self .config_by_operation .get (self .config_story_operation ,self .config )
            self .integer_result =op_cfg .get ("risultato_intero",True )
            self .show_story ()
        else :
            self .start_level ()

    def effective_level (self ):
        return min (self .level ,len (self .levels )-1 )

    def is_last_story_level (self ):
        return self .level >=self .num_story_levels -1 

    def start_level (self ):
        if self .mode =="auto":
            lv =self .effective_level ()
            self .questions_per_level =random .randint (8 +lv ,15 +lv )
        self .questions_asked =0 
        self .answer_times =[]
        self .monster_times =[]
        self .boss_times =[]
        self .current_block =[]
        self .timeout_handled =False 
        if self .player_entrance :
            self .character_entry =True 
            self .character_entry_start =pygame .time .get_ticks ()
            start_x =-100 if self .player_in_dir =="sx"else SCREEN_WIDTH +80 
            self .character_entry_x =start_x 
        else :
            self .new_question ()

    def show_story (self ):
        if self .story_idx >=len (self .story_entries ):
            self .state ="gameover"
            return 
        entry =self .story_entries [self .story_idx ]
        if not isinstance (entry ,dict ):
            entry ={"tipo":"testo","testo":str (entry )}
        entry_type =entry .get ("tipo","testo")
        if entry_type =="livello":
            self .state ="story"
            self .story_is_level =True 
            self .story_monsters =entry .get ("monsters",list (range (1 ,9 )))
            self .story_flying_monsters =entry .get ("flying",[])
            bg_name =entry .get ("bg","game")
            self .story_next_bg =self .backgrounds .get (bg_name ,self .bg )
            self .player_in_dir =entry .get ("player_in","sx")
            self .player_out_dir =entry .get ("player_out","dx")
            self .player_entrance =entry .get ("player_entrance","y")=="y"
            self .monster_in_dir =entry .get ("monster_in","dx")
            self .player_flip =(self .player_in_dir =="dx")
            self .player_stand_x =(SCREEN_WIDTH -75 -self .char_w )if self .player_flip else 75 

            boss_name =entry .get ("boss")
            if boss_name and self .boss_data :
                self .boss_active =True 
                self .boss_phase =None 
                self .boss_in_dir =entry .get ("boss_in","dx")
                self .boss_flip =(self .boss_in_dir =="dx")
                self .boss_frames =[pygame .transform .flip (f ,True ,False )for f in self .boss_data ["walk"]]if self .boss_flip else self .boss_data ["walk"]
                self .boss_hit_img =pygame .transform .flip (self .boss_data ["hit"],True ,False )if self .boss_flip else self .boss_data ["hit"]
                self .boss_defeated_img =pygame .transform .flip (self .boss_data ["defeated"],True ,False )if self .boss_flip else self .boss_data ["defeated"]
                self .boss_hit =False 
                self .boss_fade_start =0 
                self .boss_questions_asked =0 
                self .boss_progress =0.0 
                self .boss_anim_frame =0 
                boss_w =self .boss_hit_img .get_width ()
                if self .boss_in_dir =="dx":
                    self .boss_end_x =float (SCREEN_WIDTH -75 -boss_w )
                    self .boss_start_x =float (SCREEN_WIDTH +30 )
                else :
                    self .boss_end_x =75.0 
                    self .boss_start_x =float (-boss_w -30 )
                self .boss_x =self .boss_start_x 
            else :
                self .boss_active =False 

            self .story_text_full =""
            self .story_characters_shown =0 
            if self .story_fade_alpha >=255 :
                self .game_bg =self .story_next_bg 
                self .story_phase ="enter"
                self .story_fade_alpha =255 
                self .story_fade_speed =8 
            else :
                self .story_fade_alpha =0 
                self .story_fade_color =(0 ,0 ,0 )
                self .story_phase ="exit"
                self .story_fade_speed =8 
        else :
            self .state ="story"
            raw_text =entry .get ("testo","")
            raw_text =raw_text .replace ("NOMEPROFILOINUSO",self .current_profile )
            m =self .config_gender =="M"
            self .story_text_full =re .sub (r'-([^-]+)-([^-]+)-',lambda g :g .group (1 )if m else g .group (2 ),raw_text )
            self .story_characters_shown =0 
            self .story_typing_frame =0 
            if self .story_first_step :
                self .story_fade_alpha =255 
                self .story_fade_color =(255 ,255 ,255 )
                self .story_phase ="enter"
                self .story_fade_speed =1 
                self .story_first_step =False 
            elif self .story_fade_alpha >=255 and self .story_fade_color ==(255 ,255 ,255 ):
                self .story_fade_alpha =255 
                self .story_fade_color =(255 ,255 ,255 )
                self .story_phase ="enter"
                self .story_fade_speed =3 
            else :
                self .story_fade_alpha =80 
                self .story_fade_color =(0 ,0 ,0 )
                self .story_phase ="enter"
                self .story_fade_speed =3 

    def new_question (self ):
        if self .lives <=0 :
            return 

        if self .boss_active and self .boss_phase =="fight":
            if self .boss_questions_asked >=self .boss_total_questions :
                self .boss_phase ="defeated"
                self .boss_defeated_start =pygame .time .get_ticks ()
                self .boss_defeated_timer =0 
                return 
            self .prev_a ,self .prev_b =self .a ,self .b 
            lv =self .effective_level ()
            lv_data =self .levels [lv ]
            self .operation =self .config_story_operation 
            self .a ,self .b =select_operands (lv_data ["pool_a"],lv_data ["pool_b"],self .reinforcement_queue ,self .operation ,self .integer_result )
            if self .operation =="sottrazione"and self .a <self .b :
                self .a ,self .b =self .b ,self .a 
            if (self .a ,self .b )==(self .prev_a ,self .prev_b ):
                self .a ,self .b =self .b ,self .a 
            self .expected_result =calculate_result (self .a ,self .b ,self .operation ,self .integer_result )
            self .boss_questions_asked +=1 
            self .question_active =True 
            self .input_utente =""
            self .wait_for_enter =False 
            self .monster_hit =False 
            self .boss_hit =False 
            self .monster_img =self .monster_frames [0 ]
            if self .boss_pause_start >0 :
                self .boss_paused_ms +=pygame .time .get_ticks ()-self .boss_pause_start 
                self .boss_pause_start =0 
            self .timeout_limit =self .boss_timeout 
            self .timeout_handled =False 
            self .feedback =None 
            self .feedback_timer =0 
            self .zap_timer =0 
            self .zap_reverse =False 
            self .player_hit =False 
            self .hit_timer =0 
            self .is_correct =False 
            return 

        self .prev_a ,self .prev_b =self .a ,self .b 
        if self .mode =="auto":
            if self .questions_asked >=self .questions_per_level :
                if self .boss_active :
                    lv =self .level 
                    tempi_lv =self .stats .get (lv ,{}).get ("tempi",[])
                    if tempi_lv :
                        avg_time =sum (tempi_lv )/len (tempi_lv )
                        self .boss_timeout =max (10 ,math .ceil (avg_time )*11 )
                    else :
                        self .boss_timeout =60 
                    self .boss_phase ="shake"
                    self .boss_shake_start =pygame .time .get_ticks ()
                    self .boss_x =self .boss_start_x 
                    self .boss_entrance_start =0 
                    return 
                self .save_session ()
                self .state ="level_complete"
                return 
            lv =self .effective_level ()
            lv_data =self .levels [lv ]
            self .operation =self .config_story_operation 
            self .a ,self .b =select_operands (lv_data ["pool_a"],lv_data ["pool_b"],self .reinforcement_queue ,self .operation ,self .integer_result )
            if self .operation =="sottrazione"and self .a <self .b :
                self .a ,self .b =self .b ,self .a 
            self .questions_asked +=1 
        else :
            if self .questions_asked >=self .total_questions :
                self .save_session ()
                self .player_exit_start =pygame .time .get_ticks ()
                self .player_exit_x =75 
                self .state ="player_exit"
                return 
            self .a ,self .b =select_operands (
            self .pool_a ,
            self .pool_b ,
            self .reinforcement_queue ,
            self .operation ,
            self .integer_result ,
            self .max_sum ,
            )
            if self .swap_operandi and random .random ()<0.5 :
                if self .operation !="divisione"or not self .integer_result :
                    self .a ,self .b =self .b ,self .a 
            if self .operation =="sottrazione"and self .positive_difference and self .a <self .b :
                self .a ,self .b =self .b ,self .a 
            self .questions_asked +=1 

        if (self .a ,self .b )==(self .prev_a ,self .prev_b ):
            if self .a ==self .b :
                if self .mode =="auto":
                    lv =self .effective_level ()
                    pool_a =self .levels [lv ]["pool_a"]
                    candidates =[n for n in pool_a if n !=self .a ]
                else :
                    candidates =[n for n in self .pool_a if n !=self .a ]
                if candidates :
                    self .a =random .choice (candidates )
                    self .b =random .choice (pool_a if self .mode =="auto"else self .pool_a )
            else :
                self .a ,self .b =self .b ,self .a 
                if self .mode =="fixed"and self .operation =="sottrazione"and self .positive_difference and self .a <self .b :
                    self .a ,self .b =self .b ,self .a 

        self .expected_result =calculate_result (self .a ,self .b ,self .operation ,self .integer_result )
        if self .mode =="auto":
            mostri_disponibili =[m for m in self .monsters if m ["idx"]in self .story_monsters ]
        else :
            mostri_disponibili =self .monsters 
        scelto =random .choice ([m for m in mostri_disponibili if m is not self .previous_monster ])if len (mostri_disponibili )>1 else mostri_disponibili [0 ]
        self .previous_monster =scelto 
        self .monster_type ="fly"if scelto ["idx"]in self .story_flying_monsters else "walk"
        self .monster_y_offset =0 
        self .monster_frames =scelto ["frames"]
        self .monster_hit_img =scelto ["hit"]
        if self .monster_in_dir =="sx":
            self .monster_frames =[pygame .transform .flip (f ,True ,False )for f in self .monster_frames ]
            self .monster_hit_img =pygame .transform .flip (self .monster_hit_img ,True ,False )
        self .monster_img =self .monster_frames [0 ]
        self .input_utente =""
        self .monster_progress =0.0 
        if self .monster_in_dir =="dx":
            self .monster_start_x =SCREEN_WIDTH +30 
        else :
            self .monster_start_x =-130 
        self .monster_end_x =(self .player_stand_x -125 )if self .monster_in_dir =="sx"else 225 
        self .monster_x =self .monster_start_x 
        self .monster_hit =False 
        self .player_hit =False 
        self .monster_anim_frame =0 
        self .question_active =True 
        self .feedback =None 
        self .feedback_timer =0 
        self .zap_timer =0 
        self .zap_reverse =False 
        self .wait_for_enter =False 
        self .timeout_handled =False 
        self .question_start =pygame .time .get_ticks ()

        if self .mode =="auto":
            richieste =5 +sum (range (1 ,self .level +1 ))
            fatte =sum (1 for esito ,_ in self .current_block if esito )
            self .remaining_questions =max (richieste -fatte ,0 )

    def handle_input (self ,event ):
        if event .type ==pygame .KEYDOWN and event .key ==pygame .K_F11 :
            self .fullscreen =not self .fullscreen 
            flags =self .flags 
            if self .fullscreen :
                flags |=pygame .FULLSCREEN 
            self .screen =pygame .display .set_mode ((SCREEN_WIDTH ,SCREEN_HEIGHT ),flags )
            self .setup_cursor ()
            return 
        if self .state =="splash":
            if event .type in (pygame .KEYDOWN ,pygame .MOUSEBUTTONDOWN )and not self .splash_skip :
                self .splash_skip =True 
                self .splash_start =pygame .time .get_ticks ()
            return 
        if event .type ==pygame .KEYDOWN :
            if event .unicode and event .unicode .isalpha ():
                self .debug_buf =(self .debug_buf +event .unicode .lower ())[-5 :]
                if self .debug_buf =="debug":
                    self .debug =not self .debug 
                    self .debug_buf =""
            if self .state =="profile_select":
                if self .profile_input_mode :
                    if self .profile_gender_mode :
                        if event .key ==pygame .K_ESCAPE :
                            self .profile_gender_mode =False 
                        elif event .key ==pygame .K_f :
                            self .config_gender ="F"
                            nuovo =sanitize_profile_name (self .profile_input )
                            if not nuovo :
                                return 
                            if nuovo not in self .profiles :
                                self .profiles .append (nuovo )
                            self .save_profile_config (nuovo )
                            self .current_profile =nuovo 
                            self .update_char_image ()
                            self .save_profiles ()
                            self .profile_input =""
                            self .profile_input_mode =False 
                            self .profile_gender_mode =False 
                            self .state ="menu"
                        elif event .key ==pygame .K_m :
                            self .config_gender ="M"
                            nuovo =sanitize_profile_name (self .profile_input )
                            if not nuovo :
                                return 
                            if nuovo not in self .profiles :
                                self .profiles .append (nuovo )
                            self .save_profile_config (nuovo )
                            self .current_profile =nuovo 
                            self .update_char_image ()
                            self .save_profiles ()
                            self .profile_input =""
                            self .profile_input_mode =False 
                            self .profile_gender_mode =False 
                            self .state ="menu"
                    else :
                        if event .key ==pygame .K_ESCAPE :
                            self .profile_input_mode =False 
                            self .profile_input =""
                        elif event .key ==pygame .K_RETURN and self .profile_input .strip ():
                            self .profile_gender_mode =True 
                        elif event .key ==pygame .K_BACKSPACE :
                            self .profile_input =self .profile_input [:-1 ]
                        elif event .unicode and event .unicode .isprintable ()and len (self .profile_input )<30 :
                            self .profile_input +=event .unicode 
                    return 
                if event .key ==pygame .K_RETURN :
                    if self .profile_cursor <len (self .profiles ):
                        self .current_profile =self .profiles [self .profile_cursor ]
                        self .load_profile_config (self .current_profile )
                        self .update_char_image ()
                        self .save_profiles ()
                        self .state ="menu"
                    else :
                        self .profile_input_mode =True 
                        self .profile_input =""
                elif event .key ==pygame .K_ESCAPE :
                    if self .profiles :
                        self .state ="menu"
                    else :
                        self .running =False 
            elif self .state =="menu":
                if event .key ==pygame .K_RETURN :
                    self .mode ="auto"if self .menu_cursor ==0 else "fixed"
                    self .start_game ()
                elif event .key ==pygame .K_1 :
                    self .mode ="auto"
                    self .start_game ()
                elif event .key ==pygame .K_2 :
                    self .mode ="fixed"
                    self .start_game ()
                elif event .key ==pygame .K_o :
                    self .state ="options"
                elif event .key ==pygame .K_p :
                    if self .current_profile in self .profiles :
                        self .profile_cursor =self .profiles .index (self .current_profile )
                    else :
                        self .profile_cursor =0 
                    self .state ="profile_select"
                elif event .key ==pygame .K_ESCAPE :
                    self .running =False 
            elif self .state =="options":
                if event .key ==pygame .K_1 :
                    self .state ="options_auto"
                elif event .key ==pygame .K_2 :
                    self .show_config ()
                elif event .key ==pygame .K_RETURN :
                    if self .options_cursor ==0 :
                        self .state ="options_auto"
                    else :
                        self .show_config ()
                elif event .key ==pygame .K_ESCAPE :
                    self .state ="menu"
            elif self .state =="options_auto":
                if event .key in (pygame .K_UP ,pygame .K_w ):
                    self .options_cursor =(self .options_cursor -1 )%3 
                elif event .key in (pygame .K_DOWN ,pygame .K_s ):
                    self .options_cursor =(self .options_cursor +1 )%3 
                elif event .key in (pygame .K_PLUS ,pygame .K_EQUALS ,pygame .K_KP_PLUS ):
                    if self .options_cursor ==0 :
                        self .auto_timeout =min (99 ,self .auto_timeout +1 )
                    elif self .options_cursor ==1 :
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 )-1 )
                        self .initial_level =min (prog_max ,self .initial_level +1 )
                    else :
                        ops =["moltiplicazione","addizione","sottrazione","divisione"]
                        idx =(ops .index (self .config_story_operation )+1 )%4 
                        self .config_story_operation =ops [idx ]
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 )-1 )
                        self .initial_level =min (self .initial_level ,prog_max )
                    self .save_profile_config ()
                elif event .key in (pygame .K_MINUS ,pygame .K_KP_MINUS ):
                    if self .options_cursor ==0 :
                        self .auto_timeout =max (3 ,self .auto_timeout -1 )
                    elif self .options_cursor ==1 :
                        self .initial_level =max (0 ,self .initial_level -1 )
                    else :
                        ops =["moltiplicazione","addizione","sottrazione","divisione"]
                        idx =(ops .index (self .config_story_operation )-1 )%4 
                        self .config_story_operation =ops [idx ]
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 )-1 )
                        self .initial_level =min (self .initial_level ,prog_max )
                    self .save_profile_config ()
                elif event .key in (pygame .K_RETURN ,pygame .K_KP_ENTER ):
                    self .save_profile_config ()
                    self .state ="menu"
                elif event .key ==pygame .K_ESCAPE :
                    self .state ="options"
            elif self .state =="config_fixed":
                self .handle_config (event )
            elif self .state =="game":
                if self .game_over :
                    if event .key ==pygame .K_r :
                        self .start_game ()
                        return 
                    elif event .key ==pygame .K_m :
                        self .save_session ()
                        self .state ="menu"
                        return 
                    elif event .key ==pygame .K_ESCAPE :
                        self .save_session ()
                        self .state ="menu"
                        return 
                if event .key ==pygame .K_ESCAPE :
                    self .state ="menu"
                elif self .wait_for_enter and event .key in (pygame .K_RETURN ,pygame .K_KP_ENTER ):
                    if self .game_over :
                        self .save_session ()
                        self .state ="gameover"
                    else :
                        self .new_question ()
                elif self .question_active :
                    if event .key in (pygame .K_RETURN ,pygame .K_KP_ENTER )and self .input_utente :
                        self .check_answer ()
                    elif event .key ==pygame .K_BACKSPACE :
                        self .input_utente =self .input_utente [:-1 ]
                    elif event .key in NUMPAD_DIGIT :
                        if len (self .input_utente )<6 :
                            self .input_utente +=str (NUMPAD_DIGIT [event .key ])
                    elif event .key ==pygame .K_KP_MINUS and not self .input_utente :
                        self .input_utente +="-"
                    elif event .unicode =="."and self .operation =="divisione"and not self .integer_result and "."not in self .input_utente and len (self .input_utente )<6 :
                        self .input_utente +="."
                    elif event .unicode .isdigit ()and len (self .input_utente )<6 :
                        self .input_utente +=event .unicode 
                    elif event .unicode =="-"and not self .input_utente :
                        self .input_utente +=event .unicode 
            elif self .state =="gameover":
                if event .key ==pygame .K_r :
                    self .start_game ()
                elif event .key ==pygame .K_m :
                    self .state ="menu"
                elif event .key ==pygame .K_ESCAPE :
                    self .running =False 
            elif self .state =="level_complete":
                if event .key in (pygame .K_RETURN ,pygame .K_KP_ENTER ):
                    richieste =5 +self .level 
                    recent_times =self .monster_times [-richieste :]
                    average =sum (recent_times )/len (recent_times )if recent_times else 0 
                    if not self .is_last_story_level ():
                        self .level +=1 
                        if self .level >self .story_progress .get (self .config_story_operation ,0 ):
                            self .story_progress [self .config_story_operation ]=self .level 
                            self .save_profile_config ()
                        if average <self .timeout_limit /2 :
                            self .timeout_limit =max (3 ,self .timeout_limit -1 )
                    self .return_to_game =True 
                    self .player_exit_start =pygame .time .get_ticks ()
                    self .player_exit_x =75 
                    self .state ="player_exit"
            elif self .state =="story":
                if event .key in (pygame .K_RETURN ,pygame .K_KP_ENTER ,pygame .K_SPACE ):
                    if self .story_phase =="show":
                        if self .story_characters_shown <len (self .story_text_full ):
                            self .story_characters_shown =len (self .story_text_full )
                        else :
                            self .story_fade_speed =3 
                            self .story_phase ="exit"

        if event .type ==pygame .MOUSEBUTTONDOWN :
            mx ,my =event .pos 
            if self .state =="story":
                if self .story_phase =="show":
                    if self .story_characters_shown <len (self .story_text_full ):
                        self .story_characters_shown =len (self .story_text_full )
                    else :
                        self .story_fade_speed =3 
                        self .story_phase ="exit"
            elif self .state =="gameover":
                if hasattr (self ,'gameover_buttons'):
                    if self .gameover_buttons .get ("restart")and self .gameover_buttons ["restart"].collidepoint (mx ,my ):
                        self .player_exit_retry =True 
                        self .player_exit_start =pygame .time .get_ticks ()
                        self .player_exit_x =75 
                        self .state ="player_exit"
                        return 
                    if self .gameover_buttons .get ("menu")and self .gameover_buttons ["menu"].collidepoint (mx ,my ):
                        self .state ="menu"
                        return 
            if self .state =="menu":
            # Opzione 1: Storia (midleft 340, 280)
                if 340 -10 <=mx <=340 +580 and 280 -10 <=my <=280 +74 :
                    self .mode ="auto"
                    self .start_game ()
                    # Opzione 2: Allenamento (midleft 340, 380)
                elif 340 -10 <=mx <=340 +580 and 380 -10 <=my <=380 +74 :
                    self .mode ="fixed"
                    self .start_game ()
                    # Gear icon (centro 1235, 45, raggio 22)
                elif (mx -1235 )**2 +(my -45 )**2 <=(22 +10 )**2 :
                    self .state ="options"
                    # Profilo (midleft 340, 550)
                elif 340 -10 <=mx <=340 +400 and 550 -10 <=my <=550 +34 :
                    if self .current_profile in self .profiles :
                        self .profile_cursor =self .profiles .index (self .current_profile )
                    else :
                        self .profile_cursor =0 
                    self .state ="profile_select"
            elif self .state =="profile_select":
                if not self .profile_input_mode :
                    voci =self .profiles +["Nuovo profilo"]
                    for i ,voce in enumerate (voci ):
                        y =170 +i *60 
                        txt =self .font_large .render (voce ,True ,WHITE )
                        rect =txt .get_rect (midleft =(SCREEN_WIDTH //2 -200 ,y ))
                        if rect .collidepoint (mx ,my ):
                            if i <len (self .profiles ):
                                self .current_profile =self .profiles [i ]
                                self .load_profile_config (self .profiles [i ])
                                self .update_char_image ()
                                self .save_profiles ()
                                self .state ="menu"
                            else :
                                self .profile_input_mode =True 
                                self .profile_input =""
                            break 
                elif self .profile_gender_mode :
                    for i ,key in enumerate (("F","M")):
                        sx =SCREEN_WIDTH //2 -310 +i *340 
                        y =370 
                        prof_img =self .char_data [key ]["profile"]
                        img_w ,img_h =prof_img .get_size ()
                        box_h =max (90 ,img_h +20 )
                        box_rect =pygame .Rect (sx ,y ,280 ,box_h )
                        if box_rect .collidepoint (mx ,my ):
                            self .config_gender =key 
                            nuovo =sanitize_profile_name (self .profile_input )
                            if not nuovo :
                                return 
                            if nuovo not in self .profiles :
                                self .profiles .append (nuovo )
                            self .save_profile_config (nuovo )
                            self .current_profile =nuovo 
                            self .update_char_image ()
                            self .save_profiles ()
                            self .profile_input =""
                            self .profile_input_mode =False 
                            self .profile_gender_mode =False 
                            self .state ="menu"
                            break 
            elif self .state =="options":
                if SCREEN_WIDTH //2 -320 <=mx <=SCREEN_WIDTH //2 +320 :
                    if 209 <=my <=273 :
                        self .state ="options_auto"
                    elif 289 <=my <=353 :
                        self .show_config ()
            elif self .state =="options_auto":
                sx =360 
                lw ,vw ,rw =30 ,40 ,30 
                # Timeout
                if sx -2 <=mx <=sx +lw +vw +rw +2 and 198 <=my <=236 :
                    self .options_cursor =0 
                    if mx <sx +lw :
                        self .auto_timeout =max (3 ,self .auto_timeout -1 )
                    elif mx >=sx +lw +vw :
                        self .auto_timeout =min (99 ,self .auto_timeout +1 )
                    self .save_profile_config ()
                    # Livello iniziale
                elif sx -2 <=mx <=sx +lw +vw +rw +2 and 268 <=my <=306 :
                    self .options_cursor =1 
                    if mx <sx +lw :
                        self .initial_level =max (0 ,self .initial_level -1 )
                    elif mx >=sx +lw +vw :
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 )-1 )
                        self .initial_level =min (prog_max ,self .initial_level +1 )
                    self .save_profile_config ()
                    # Operazione — 4 pulsanti
                if hasattr (self ,'opzioni_auto_op_buttons')and len (self .opzioni_auto_op_buttons )==4 :
                    ops =["moltiplicazione","addizione","sottrazione","divisione"]
                    for i ,btn in enumerate (self .opzioni_auto_op_buttons ):
                        if btn .collidepoint (mx ,my ):
                            self .options_cursor =2 
                            self .config_story_operation =ops [i ]
                            prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 )-1 )
                            self .initial_level =min (self .initial_level ,prog_max )
                            self .save_profile_config ()
                            break 
                            # CONFERMA
                if SCREEN_WIDTH //2 -110 <=mx <=SCREEN_WIDTH //2 +110 and 418 <=my <=468 :
                    self .save_profile_config ()
                    self .state ="menu"
            elif self .state =="config_fixed":
                try :
                    self .handle_config (event )
                except Exception as e :
                    print (f"config mouse error: {e }")
                    import traceback 
                    traceback .print_exc ()

    def handle_config (self ,event ):
        ops =["moltiplicazione","addizione","sottrazione","divisione"]
        op_idx =ops .index (self .config_operation )
        addition =self .config_operation =="addizione"
        subtraction =self .config_operation =="sottrazione"
        division =self .config_operation =="divisione"
        pools_mode =addition or subtraction or division 
        cols_u =5 
        pool_items =10 if pools_mode else 13 

        def row_y (r ):
            base =[150 ,210 ,290 ,370 ,420 ,470 ,520 ,550 ]
            cell_h ,gap =30 ,6 
            subrows_pool =(pool_items +4 )//5 
            pool_extra =max (0 ,(subrows_pool -2 ))*(cell_h +gap )
            offset =0 
            if r >=2 :
                offset +=pool_extra 
            if r >=3 :
                offset +=pool_extra 
            return base [r ]+offset 

        def pool_ncols ():
            if pools_mode :
                return (10 ,5 )
            return (13 ,5 )

        def pool_rows ():
            items ,cols =pool_ncols ()
            return (items +cols -1 )//cols 

        def pool_index (subrow ,col ):
            items ,cols =pool_ncols ()
            idx =subrow *cols +col 
            return idx if idx <items else -1 

        def max_col_for_row (r ):
            if r in (1 ,2 ):
                return 4 
            return 0 

        def skip_sum (r ,step ):
            if not addition and not subtraction and not division :
                if step ==1 and r ==2 :
                    return 4 
                if step ==-1 and r ==4 :
                    return 2 
            return r 

        if event .type ==pygame .MOUSEBUTTONDOWN :
            mx ,my =event .pos 

            # Row 7: CONFERMA
            y7 =row_y (7 )
            if SCREEN_WIDTH //2 -110 <=mx <=SCREEN_WIDTH //2 +110 and y7 <=my <=y7 +46 :
                self .save_profile_config ()
                self .state ="menu"
                return 

                # Row 0: operation selector
            y0 =row_y (0 )
            if y0 -2 <=my <=y0 +36 :
                for i in range (4 ):
                    sx =360 +i *170 
                    if sx <=mx <=sx +158 :
                        self .config_operation =ops [i ]
                        self .config =self .config_by_operation [self .config_operation ]
                        self .config_cursor_row =0 
                        self .config_cursor_col =0 
                        self .config_cursor_subrow =0 
                        return 

                        # Row 1 and 2: pool grid
            for ri in range (2 ):
                r =1 +ri 
                y_base =row_y (r )
                subrows =(pool_items +cols_u -1 )//cols_u 
                cell_w ,cell_h =100 ,30 
                gap =6 
                grid_x =360 
                for sr in range (subrows ):
                    sy =y_base +sr *(cell_h +gap )
                    for c in range (cols_u ):
                        idx =sr *cols_u +c 
                        if idx >=pool_items :
                            break 
                        sx =grid_x +c *(cell_w +gap )
                        if sx -2 <=mx <=sx +cell_w +2 and sy -2 <=my <=sy +cell_h +2 :
                            self .config_cursor_row =r 
                            self .config_cursor_col =c 
                            self .config_cursor_subrow =sr 
                            pool =self .config ["pool_a"]if r ==1 else self .config ["pool_b"]
                            if pools_mode :
                                start =idx *10 
                                if not (any (pool [start :start +10 ])and sum (pool )==10 ):
                                    new_state =not any (pool [start :start +10 ])
                                    for i in range (start ,start +10 ):
                                        pool [i ]=new_state 
                            else :
                                if not (pool [idx ]and sum (pool )==1 ):
                                    pool [idx ]=not pool [idx ]
                            return 

                            # Row 3: somma massima (addizione) / differenza positiva (sottrazione)
            y3 =row_y (3 )
            if y3 -2 <=my <=y3 +36 :
                if addition :
                    lw =30 
                    if 360 -2 <=mx <=360 +100 +2 :
                        self .config_cursor_row =3 
                        self .config_cursor_col =0 
                        if mx <360 +lw :
                            self .config ["somma_massima"]=max (1 ,self .config ["somma_massima"]-1 )
                        elif mx >=360 +lw +40 :
                            self .config ["somma_massima"]=min (199 ,self .config ["somma_massima"]+1 )
                        return 
                elif subtraction :
                    if 350 <=mx <=540 and y3 -4 <=my <=y3 +40 :
                        self .config_cursor_row =3 
                        self .config_cursor_col =0 
                        self .config ["differenza_positiva"]=not self .config ["differenza_positiva"]
                        return 
                elif division :
                    if 350 <=mx <=540 and y3 -4 <=my <=y3 +40 :
                        self .config_cursor_row =3 
                        self .config_cursor_col =0 
                        self .config ["risultato_intero"]=not self .config ["risultato_intero"]
                        return 

                        # Row 4: domande
            y4 =row_y (4 )
            if y4 -2 <=my <=y4 +36 :
                lw =30 
                if 360 -2 <=mx <=360 +100 +2 :
                    self .config_cursor_row =4 
                    self .config_cursor_col =0 
                    if mx <360 +lw :
                        self .config ["domande"]=max (1 ,self .config ["domande"]-1 )
                    elif mx >=360 +lw +40 :
                        self .config ["domande"]=min (99 ,self .config ["domande"]+1 )
                    return 

                    # Row 5: swap
            y5 =row_y (5 )
            if y5 -4 <=my <=y5 +40 :
                if 350 <=mx <=540 and not subtraction :
                    self .config_cursor_row =5 
                    self .config_cursor_col =0 
                    self .config ["swap"]=not self .config ["swap"]
                    return 

                    # Row 6: timeout
            y6 =row_y (6 )
            if y6 -2 <=my <=y6 +36 :
                lw =30 
                if 360 -2 <=mx <=360 +100 +2 :
                    self .config_cursor_row =6 
                    self .config_cursor_col =0 
                    if mx <360 +lw :
                        self .config ["timeout"]=max (3 ,self .config ["timeout"]-1 )
                    elif mx >=360 +lw +40 :
                        self .config ["timeout"]=min (99 ,self .config ["timeout"]+1 )
                    return 

            return 

        if event .key ==pygame .K_ESCAPE :
            self .state ="options"
            return 
        if event .key ==pygame .K_RETURN :
            self .save_profile_config ()
            self .state ="menu"
            return 

        row =self .config_cursor_row 
        col =self .config_cursor_col 
        sub =self .config_cursor_subrow 

        if event .key ==pygame .K_UP :
            if row in (1 ,2 ):
                if sub >0 :
                    sub -=1 
                else :
                    row =skip_sum (max (0 ,row -1 ),-1 )
            else :
                row =skip_sum (max (0 ,row -1 ),-1 )
            self .config_cursor_col =min (col ,max_col_for_row (row ))
        elif event .key ==pygame .K_DOWN :
            if row in (1 ,2 ):
                if sub <pool_rows ()-1 :
                    idx =pool_index (sub +1 ,col )
                    if idx >=0 :
                        sub +=1 
                    else :
                        row =skip_sum (min (7 ,row +1 ),1 )
                else :
                    row =skip_sum (min (7 ,row +1 ),1 )
            else :
                row =skip_sum (min (7 ,row +1 ),1 )
            self .config_cursor_col =min (col ,max_col_for_row (row ))
        elif event .key ==pygame .K_LEFT :
            if row ==0 :
                self .config_operation =ops [(op_idx -1 )%4 ]
                self .config =self .config_by_operation [self .config_operation ]
            elif row in (1 ,2 ):
                if col >0 :
                    col -=1 
                else :
                    col =max_col_for_row (row )
            else :
                self .config_cursor_col =max (0 ,col -1 )
        elif event .key ==pygame .K_RIGHT :
            if row ==0 :
                self .config_operation =ops [(op_idx +1 )%4 ]
                self .config =self .config_by_operation [self .config_operation ]
            elif row in (1 ,2 ):
                if col <4 :
                    idx =pool_index (sub ,col +1 )
                    if idx >=0 :
                        col +=1 
            else :
                self .config_cursor_col =min (max_col_for_row (row ),col +1 )
        elif event .key ==pygame .K_SPACE :
            if row ==0 :
                self .config_operation =ops [(op_idx +1 )%4 ]
                self .config =self .config_by_operation [self .config_operation ]
            elif row in (1 ,2 ):
                pool =self .config ["pool_a"]if row ==1 else self .config ["pool_b"]
                idx =pool_index (sub ,col )
                if idx >=0 :
                    if pools_mode :
                        start =idx *10 
                        if not (any (pool [start :start +10 ])and sum (pool )==10 ):
                            new_state =not any (pool [start :start +10 ])
                            for i in range (start ,start +10 ):
                                pool [i ]=new_state 
                    else :
                        if not (pool [idx ]and sum (pool )==1 ):
                            pool [idx ]=not pool [idx ]
            elif row ==3 and subtraction :
                self .config ["differenza_positiva"]=not self .config ["differenza_positiva"]
            elif row ==3 and division :
                self .config ["risultato_intero"]=not self .config ["risultato_intero"]
            elif row ==5 and not subtraction :
                self .config ["swap"]=not self .config ["swap"]
        elif event .key in (pygame .K_PLUS ,pygame .K_EQUALS ,pygame .K_KP_PLUS ):
            if row ==3 and addition :
                self .config ["somma_massima"]=min (199 ,self .config ["somma_massima"]+1 )
            elif row ==4 :
                self .config ["domande"]=min (99 ,self .config ["domande"]+1 )
            elif row ==6 :
                self .config ["timeout"]=min (99 ,self .config ["timeout"]+1 )
        elif event .key in (pygame .K_MINUS ,pygame .K_KP_MINUS ):
            if row ==3 and addition :
                self .config ["somma_massima"]=max (1 ,self .config ["somma_massima"]-1 )
            elif row ==4 :
                self .config ["domande"]=max (1 ,self .config ["domande"]-1 )
            elif row ==6 :
                self .config ["timeout"]=max (3 ,self .config ["timeout"]-1 )

        self .config_cursor_row =row 
        self .config_cursor_col =col 
        self .config_cursor_subrow =sub 

    def check_answer (self ):
        if not self .question_active :
            return 

        elapsed_time =min ((pygame .time .get_ticks ()-self .question_start )/1000.0 ,self .timeout_limit )
        self .answer_times .append (elapsed_time )
        if self .boss_active and self .boss_phase =="fight":
            self .boss_times .append (elapsed_time )
        else :
            self .monster_times .append (elapsed_time )

        level =0 if self .mode =="fixed"else self .level 
        self .stats .setdefault (level ,{"corrette":0 ,"sbagliate":0 ,"tempi":[]})

        text_value =self .input_utente .strip ()
        risposta =None 
        try :
            if "."in text_value :
                risposta =float (text_value )
            else :
                risposta =int (text_value )
        except ValueError :
            risposta =None 

        if risposta is not None and is_answer_correct (risposta ,self .expected_result ):
            self .is_correct =True 
            self .stats [level ]["corrette"]+=1 
            if self .boss_active and self .boss_phase =="fight":
                self .boss_hit =True 
                self .boss_hit_start =pygame .time .get_ticks ()
                self .zap_timer =12 
            else :
                self .monster_hit =True 
                self .monster_fade_start =pygame .time .get_ticks ()
                self .monster_img =self .monster_hit_img 
                self .zap_timer =12 
        else :
            self .is_correct =False 
            self .stats [level ]["sbagliate"]+=1 
            self .lives -=1 
            if self .boss_active and self .boss_phase =="fight":
                self .boss_total_questions +=1 
            self .monster_hit =True 
            self .monster_fade_start =pygame .time .get_ticks ()
            self .monster_img =self .monster_hit_img 
            self .zap_timer =12 
            self .zap_reverse =True 
            self .player_hit =True 
            self .current_block .clear ()
            for _ in range (3 ):
                self .reinforcement_queue .append ((self .a ,self .b ))
            self .hit_timer =12 

        if self .lives <=0 :
            self .game_over =True 

        if self .is_correct :
            self .consecutive_correct +=1 
            if self .consecutive_correct >=30 and self .lives <WIZARD_LIVES and not self .game_over and not (self .boss_active and self .boss_phase =="fight"):
                self .lives +=1 
                self .consecutive_correct =0 
                self .heart_reward_active =True 
                self .heart_reward_start =pygame .time .get_ticks ()
            elif self .consecutive_correct >=30 :
                self .consecutive_correct =0 
        else :
            self .consecutive_correct =0 

        self .current_block .append ((self .is_correct ,elapsed_time ))
        self .stats [level ]["tempi"].append (elapsed_time )
        self .question_active =False 
        self .feedback =self .is_correct 
        self .feedback_timer =pygame .time .get_ticks ()
        if self .boss_active and self .boss_phase =="fight":
            self .boss_pause_start =pygame .time .get_ticks ()
        if not self .is_correct :
            self .wait_for_enter =True 

    def handle_timeout (self ):
        if self .timeout_handled :
            return 
        self .timeout_handled =True 
        elapsed_time =self .timeout_limit 
        self .answer_times .append (elapsed_time )
        if self .boss_active and self .boss_phase =="fight":
            self .boss_times .append (elapsed_time )
        else :
            self .monster_times .append (elapsed_time )
        level =0 if self .mode =="fixed"else self .level 
        self .stats .setdefault (level ,{"corrette":0 ,"sbagliate":0 ,"tempi":[]})
        self .stats [level ]["sbagliate"]+=1 
        self .stats [level ]["tempi"].append (elapsed_time )
        self .lives -=1 
        self .current_block .clear ()
        for _ in range (3 ):
            self .reinforcement_queue .append ((self .a ,self .b ))
        self .is_correct =False 
        self .question_active =False 
        self .feedback =False 
        self .feedback_timer =pygame .time .get_ticks ()
        if self .boss_active and self .boss_phase =="fight":
            self .boss_pause_start =pygame .time .get_ticks ()
        self .wait_for_enter =True 
        self .monster_hit =True 
        self .monster_fade_start =pygame .time .get_ticks ()
        self .monster_img =self .monster_hit_img 
        self .zap_timer =12 
        self .zap_reverse =True 
        self .player_hit =True 
        self .hit_timer =12 
        self .consecutive_correct =0 
        if self .boss_active and self .boss_phase =="fight":
            self .lives =0 
            self .game_over =True 
        elif self .lives <=0 :
            self .game_over =True 

    def update (self ):
        if self .zap_timer >0 :
            self .zap_timer -=1 
            if self .zap_timer ==0 :
                self .zap_reverse =False 
        if self .hit_timer >0 :
            self .hit_timer -=1 
        if self .state =="splash":
            elapsed =pygame .time .get_ticks ()-self .splash_start 
            if (self .splash_skip and elapsed >=500 )or elapsed >=5000 :
                self .state ="profile_select"
            return 
        if self .state =="gameover":
            return 
        if self .state =="player_exit":
            elapsed =pygame .time .get_ticks ()-self .player_exit_start 
            if elapsed >=4000 :
                if self .player_exit_retry :
                    self .player_exit_retry =False 
                    self .lives =WIZARD_LIVES 
                    self .game_over =False 
                    self .is_correct =0 
                    self .stats ={}
                    self .timeout_limit =self .auto_timeout 
                    self .boss_phase =None 
                    self .boss_hit =False 
                    self .boss_progress =0.0 
                    self .boss_questions_asked =0 
                    self .boss_total_questions =10 
                    self .boss_timeout =60 
                    self .boss_paused_ms =0 
                    self .boss_pause_start =0 
                    self .state ="game"
                    self .start_level ()
                elif self .mode =="auto"and self .return_to_game :
                    self .return_to_game =False 
                    if self .story_entries :
                        self .story_idx +=1 
                        self .show_story ()
                    else :
                        self .start_level ()
                else :
                    self .state ="gameover"
            return 
        if self .state =="level_complete":
            return 
        if self .state =="story":
            if self .story_phase =="enter":
                self .story_fade_alpha =max (0 ,self .story_fade_alpha -self .story_fade_speed )
                if self .story_fade_alpha ==0 :
                    if self .story_is_level :
                        self .story_is_level =False 
                        self .state ="game"
                        self .start_level ()
                        return 
                    self .story_phase ="show"
            elif self .story_phase =="show":
                if self .story_characters_shown <len (self .story_text_full ):
                    self .story_typing_frame +=1 
                    if self .story_typing_frame >=2 :
                        self .story_typing_frame =0 
                        self .story_characters_shown +=1 
            elif self .story_phase =="exit":
                self .story_fade_alpha =min (255 ,self .story_fade_alpha +self .story_fade_speed )
                if self .story_fade_alpha >=255 :
                    if self .story_is_level :
                        self .game_bg =self .story_next_bg 
                        self .story_phase ="enter"
                        self .story_fade_alpha =255 
                        self .story_fade_speed =8 
                    else :
                        if self .initial_level >0 :
                            cnt =0 
                            skip_to =None 
                            for i ,e in enumerate (self .story_entries ):
                                if e ["tipo"]=="livello":
                                    if cnt ==self .initial_level :
                                        skip_to =i 
                                        break 
                                    cnt +=1 
                            self .story_idx =skip_to if skip_to is not None else self .story_idx +1 
                        else :
                            self .story_idx +=1 
                        self .show_story ()
            return 
        if self .state not in ("game",):
            return 

        if self .character_entry :
            elapsed =pygame .time .get_ticks ()-self .character_entry_start 
            duration =1200 
            progress =min (elapsed /duration ,1.0 )
            end_x =self .player_stand_x 
            start_x =-100 if self .player_in_dir =="sx"else SCREEN_WIDTH +80 
            self .character_entry_x =start_x +(end_x -start_x )*progress 
            if progress >=1.0 :
                self .character_entry =False 
                self .new_question ()
            return 

        if self .boss_active and self .boss_phase =="shake":
            elapsed =pygame .time .get_ticks ()-self .boss_shake_start 
            duration =600 
            if elapsed >=duration :
                self .boss_phase ="entrance"
                self .boss_entrance_start =pygame .time .get_ticks ()
            return 

        if self .boss_active and self .boss_phase =="entrance":
            elapsed =pygame .time .get_ticks ()-self .boss_entrance_start 
            duration =800 
            progress =min (elapsed /duration ,1.0 )
            ease =1 -(1 -progress )**3 
            self .boss_x =self .boss_start_x +(self .boss_end_x -self .boss_start_x )*ease 
            if progress >=1.0 :
                self .boss_phase ="fight"
                self .boss_progress =0.0 
                self .boss_questions_asked =0 
                self .boss_hit =False 
                self .boss_paused_ms =0 
                self .boss_pause_start =0 
                self .question_start =pygame .time .get_ticks ()
                self .new_question ()
            return 

        if self .boss_active and self .boss_phase =="fight":
            if self .boss_hit :
                hit_elapsed =pygame .time .get_ticks ()-self .boss_hit_start 
                if hit_elapsed >500 :
                    self .boss_hit =False 
            if self .question_active :
                elapsed =(pygame .time .get_ticks ()-self .question_start -self .boss_paused_ms )/1000.0 
                self .boss_progress =min (elapsed /self .boss_timeout ,1.0 )
                boss_w =self .boss_hit_img .get_width ()
                fight_end =float (self .player_stand_x -boss_w +100 )if self .boss_end_x <self .player_stand_x else float (self .player_stand_x +self .char_w -100 )
                self .boss_x =self .boss_end_x +(fight_end -self .boss_end_x )*self .boss_progress 
                if not self .boss_hit :
                    self .boss_anim_frame =(pygame .time .get_ticks ()//self .boss_anim_speed )%len (self .boss_frames )
                if self .boss_progress >=1.0 :
                    self .handle_timeout ()
            else :
                if not self .wait_for_enter :
                    if self .feedback is not None and pygame .time .get_ticks ()-self .feedback_timer >1500 :
                        if self .game_over :
                            self .save_session ()
                            self .state ="gameover"
                        else :
                            self .new_question ()
            return 

        if self .boss_active and self .boss_phase =="defeated":
            elapsed =pygame .time .get_ticks ()-self .boss_defeated_start 
            if elapsed <1500 :
                self .boss_defeated_timer =elapsed 
            else :
                fade_elapsed =elapsed -1500 
                alpha =max (0 ,255 -int (fade_elapsed /1500 *255 ))
                if alpha <=0 :
                    self .boss_active =False 
                    self .boss_phase =None 
                    self .save_session ()
                    self .state ="level_complete"
            return 

        if self .question_active :
            elapsed =(pygame .time .get_ticks ()-self .question_start )/1000.0 
            self .monster_progress =min (elapsed /self .timeout_limit ,1.0 )
            self .monster_x =self .monster_start_x +(self .monster_end_x -self .monster_start_x )*self .monster_progress 
            if self .monster_type =="fly":
                self .monster_y_offset =30 *math .sin (self .monster_progress *6 *math .pi )
            else :
                self .monster_y_offset =0 

            if self .monster_progress >=1.0 :
                self .handle_timeout ()
        else :
            if self .wait_for_enter :
                return 
            if self .feedback is not None and pygame .time .get_ticks ()-self .feedback_timer >1500 :
                if self .game_over :
                    self .save_session ()
                    self .state ="gameover"
                else :
                    self .new_question ()

    def draw (self ):
        if self .state =="splash":
            self .draw_splash ()
        elif self .state =="profile_select":
            self .screen .blit (self .bg_menu ,(0 ,0 ))
            self .draw_profile ()
        elif self .state =="game":
            self .draw_game ()
        elif self .state =="player_exit":
            self .draw_player_exit ()
        elif self .state =="level_complete":
            self .draw_level_complete ()
        elif self .state =="story":
            self .draw_story ()
        else :
            if self .state in ("options","options_auto","config_fixed"):
                self .screen .blit (self .bg_options ,(0 ,0 ))
            else :
                self .screen .blit (self .bg_menu ,(0 ,0 ))
            if self .state =="menu":
                self .draw_menu ()
            elif self .state =="options":
                self .draw_options ()
            elif self .state =="options_auto":
                self .draw_auto_options ()
            elif self .state =="config_fixed":
                self .draw_config ()
            elif self .state in ("game","gameover"):
                self .draw_gameover ()

        pygame .display .flip ()

    def draw_text_shadow (self ,font ,text ,color ,pos =None ,center =None ,midleft =None ,midright =None ,offset =2 ):
        ombra =font .render (text ,True ,(30 ,30 ,30 ))
        surf =font .render (text ,True ,color )
        if center is not None :
            rect =surf .get_rect (center =center )
        elif midleft is not None :
            rect =surf .get_rect (midleft =midleft )
        elif midright is not None :
            rect =surf .get_rect (midright =midright )
        else :
            rect =surf .get_rect (topleft =pos )if pos else surf .get_rect ()
        self .screen .blit (ombra ,(rect .x +offset ,rect .y +offset ))
        self .screen .blit (surf ,rect )
        return rect 

    def draw_splash (self ):
        elapsed =pygame .time .get_ticks ()-self .splash_start 
        logo_rect =self .logo .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT //2 ))
        self .screen .blit (self .logo ,logo_rect )

        if self .splash_skip :
            alpha =min (255 ,int (elapsed /500 *255 ))
        elif elapsed <2000 :
            alpha =255 -int (255 *elapsed /2000 )
        elif elapsed >4000 :
            alpha =int (255 *(elapsed -4000 )/1000 )
        else :
            alpha =0 
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (alpha )
        overlay .fill (BLACK )
        self .screen .blit (overlay ,(0 ,0 ))

    def draw_profile (self ):
        mx ,my =pygame .mouse .get_pos ()
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        if self .profile_input_mode :
            if self .profile_gender_mode :
                title =self .font_title .render ("NUOVO PROFILO",True ,GOLD )
                rect =title .get_rect (center =(SCREEN_WIDTH //2 ,100 ))
                self .screen .blit (title ,rect )

                nome_label =self .font_medium .render (f"Profilo: {self .profile_input }",True ,WHITE )
                rect =nome_label .get_rect (center =(SCREEN_WIDTH //2 ,200 ))
                self .screen .blit (nome_label ,rect )

                prompt =self .font_large .render ("Seleziona il personaggio:",True ,WHITE )
                rect =prompt .get_rect (center =(SCREEN_WIDTH //2 ,300 ))
                self .screen .blit (prompt ,rect )

                for i ,key in enumerate (("F","M")):
                    sx =SCREEN_WIDTH //2 -310 +i *340 
                    y =370 
                    prof_img =self .char_data [key ]["profile"]
                    img_w ,img_h =prof_img .get_size ()
                    box_h =max (90 ,img_h +20 )
                    box_rect =pygame .Rect (sx ,y ,280 ,box_h )
                    hovered =box_rect .collidepoint (mx ,my )
                    bg_col =(80 ,80 ,100 )if hovered else (60 ,60 ,70 )
                    pygame .draw .rect (self .screen ,bg_col ,box_rect ,border_radius =8 )
                    if hovered :
                        pygame .draw .rect (self .screen ,GOLD ,box_rect ,2 ,border_radius =8 )
                    if prof_img :
                        cx =sx +(280 -img_w )//2 
                        cy =y +(box_h -img_h )//2 
                        self .screen .blit (prof_img ,(cx ,cy ))

            else :
                title =self .font_title .render ("NUOVO PROFILO",True ,GOLD )
                rect =title .get_rect (center =(SCREEN_WIDTH //2 ,120 ))
                self .screen .blit (title ,rect )

                lbl =self .font_medium .render ("Inserisci il nome:",True ,WHITE )
                rect =lbl .get_rect (center =(SCREEN_WIDTH //2 ,260 ))
                self .screen .blit (lbl ,rect )

                txt =self .profile_input +("|"if pygame .time .get_ticks ()%1000 <500 else " ")
                surf =self .font_input .render (txt ,True ,WHITE )
                box =surf .get_rect (center =(SCREEN_WIDTH //2 ,330 ))
                bg =box .inflate (40 ,16 )
                bg .width =max (bg .width ,200 )
                pygame .draw .rect (self .screen ,(40 ,40 ,60 ),bg ,border_radius =8 )
                pygame .draw .rect (self .screen ,(100 ,100 ,180 ),bg ,2 ,border_radius =8 )
                self .screen .blit (surf ,box )

                if self .profile_input :
                    hint =self .font_small .render ("",True ,GRAY )
                    rect =hint .get_rect (center =(SCREEN_WIDTH //2 ,380 ))
                    self .screen .blit (hint ,rect )
                back =self .font_small .render ("",True ,GRAY )
                rect =back .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -60 ))
                self .screen .blit (back ,rect )
            return 

        title =self .font_title .render ("SELEZIONA PROFILO",True ,GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,80 ))
        self .screen .blit (title ,rect )

        voci =self .profiles +["Nuovo profilo"]
        nuovo_idx =len (self .profiles )
        for i ,voce in enumerate (voci ):
            y =170 +i *60 
            txt =self .font_large .render (voce ,True ,WHITE )
            rect =txt .get_rect (midleft =(SCREEN_WIDTH //2 -200 ,y ))
            if rect .collidepoint (mx ,my ):
                self .profile_cursor =i 
                txt =self .font_large .render (voce ,True ,GOLD )
            self .screen .blit (txt ,rect )
            if i <nuovo_idx and voce ==self .current_profile :
                ok =self .font_small .render ("(attivo)",True ,GRAY )
                rect =ok .get_rect (midleft =(SCREEN_WIDTH //2 +150 ,y +20 ))
                self .screen .blit (ok ,rect )

    def draw_menu (self ):
        mx ,my =pygame .mouse .get_pos ()
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (180 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self .font_title .render ("MATH WIZARD",True ,GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,100 ))
        self .screen .blit (title ,rect )

        subtitle =self .font_medium .render ("Impara divertendoti!",True ,WHITE )
        rect =subtitle .get_rect (center =(SCREEN_WIDTH //2 ,160 ))
        self .screen .blit (subtitle ,rect )

        opzioni =[
        ("Storia","Affronta un'avventura nel regno di Math, con incremento automatico della difficoltà."),
        ("Allenamento","Scegli le varie impostazioni per una sfida breve a difficoltà costante"),
        ]
        for i ,(tit ,desc )in enumerate (opzioni ):
            y =280 +i *100 
            opt =self .font_large .render (tit ,True ,WHITE )
            rect =opt .get_rect (midleft =(SCREEN_WIDTH //2 -300 ,y ))
            if rect .collidepoint (mx ,my ):
                self .menu_cursor =i 
                opt =self .font_large .render (tit ,True ,GOLD )
            self .screen .blit (opt ,rect )
            desc_surf =self .font_small .render (desc ,True ,GRAY )
            rect =desc_surf .get_rect (midleft =(SCREEN_WIDTH //2 -300 ,y +40 ))
            self .screen .blit (desc_surf ,rect )

            # gear icon
        cx ,cy =SCREEN_WIDTH -45 ,45 
        gear_size =44 
        gear_scaled =pygame .transform .scale (self .gear_img ,(gear_size ,gear_size ))
        rect =gear_scaled .get_rect (center =(cx ,cy ))
        if rect .collidepoint (mx ,my ):
            pygame .draw .rect (self .screen ,GOLD ,rect .inflate (8 ,8 ),2 ,border_radius =6 )
        self .screen .blit (gear_scaled ,rect )

        profile_label =self .font_small .render (f"Profilo: {self .current_profile }",True ,GRAY )
        rect =profile_label .get_rect (midleft =(SCREEN_WIDTH //2 -300 ,550 ))
        if rect .collidepoint (mx ,my ):
            profile_label =self .font_small .render (f"Profilo: {self .current_profile }",True ,GOLD )
        self .screen .blit (profile_label ,rect )

        version_surf =self .font_tiny .render (f"v{self .version }",True ,GRAY )
        rect =version_surf .get_rect (bottomright =(SCREEN_WIDTH -8 ,SCREEN_HEIGHT -8 ))
        self .screen .blit (version_surf ,rect )

    def draw_options (self ):
        mx ,my =pygame .mouse .get_pos ()
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self .font_title .render ("OPZIONI",True ,GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,80 ))
        self .screen .blit (title ,rect )

        voci =["Storia","Allenamento"]
        for i ,voce in enumerate (voci ):
            y =220 +i *80 
            txt =self .font_large .render (voce ,True ,WHITE )
            rect =txt .get_rect (center =(SCREEN_WIDTH //2 ,y +21 ))
            if rect .collidepoint (mx ,my ):
                self .options_cursor =i 
                txt =self .font_large .render (voce ,True ,GOLD )
            self .screen .blit (txt ,rect )

        credits =[
        f"v{self .version }",
        "Concept, development, and organization: TheFactor82",
        "Development, Beta testing: SL, GA, WF",
        "Graphics: Elena",
        ]
        y =SCREEN_HEIGHT -10 -len (credits )*22 
        for line in credits :
            surf =self .font_tiny .render (line ,True ,GRAY )
            rect =surf .get_rect (bottomright =(SCREEN_WIDTH -20 ,y ))
            self .screen .blit (surf ,rect )
            y +=22 

    def draw_auto_options (self ):
        mx ,my =pygame .mouse .get_pos ()
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self .font_title .render ("OPZIONI - STORIA",True ,GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,80 ))
        self .screen .blit (title ,rect )

        # Timeout
        y =200 
        label_t =self .font_tiny .render ("Timeout (secondi)",True ,WHITE )
        rect =label_t .get_rect (midleft =(80 ,y +17 ))
        self .screen .blit (label_t ,rect )
        focused =self .options_cursor ==0 
        sx =360 
        lw ,vw ,rw =30 ,40 ,30 
        minus_rect =pygame .Rect (sx ,y ,lw ,34 )
        plus_rect =pygame .Rect (sx +lw +vw ,y ,rw ,34 )
        hover_minus =minus_rect .collidepoint (mx ,my )
        hover_plus =plus_rect .collidepoint (mx ,my )
        if focused :
            pygame .draw .rect (self .screen ,SEL_BLUE ,(sx -2 ,y -2 ,lw +vw +rw +4 ,38 ),0 ,border_radius =4 )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =4 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(sx +lw ,y ,vw ,34 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =4 )
        if hover_minus :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =4 )
        if hover_plus :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =4 )
        minus =self .font_tiny .render ("-",True ,WHITE )
        plus =self .font_tiny .render ("+",True ,WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(sx +lw //2 ,y +17 )))
        self .screen .blit (plus ,plus .get_rect (center =(sx +lw +vw +rw //2 ,y +17 )))
        t_surf =self .font_tiny .render (str (self .auto_timeout ),True ,WHITE )
        self .screen .blit (t_surf ,t_surf .get_rect (center =(sx +lw +vw //2 ,y +17 )))

        # Livello iniziale
        y =270 
        label_l =self .font_tiny .render ("Livello iniziale",True ,WHITE )
        rect =label_l .get_rect (midleft =(80 ,y +17 ))
        self .screen .blit (label_l ,rect )
        focused =self .options_cursor ==1 
        minus_rect2 =pygame .Rect (sx ,y ,lw ,34 )
        plus_rect2 =pygame .Rect (sx +lw +vw ,y ,rw ,34 )
        hover_minus2 =minus_rect2 .collidepoint (mx ,my )
        hover_plus2 =plus_rect2 .collidepoint (mx ,my )
        if focused :
            pygame .draw .rect (self .screen ,SEL_BLUE ,(sx -2 ,y -2 ,lw +vw +rw +4 ,38 ),0 ,border_radius =4 )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus2 else (70 ,70 ,80 ),minus_rect2 ,border_radius =4 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(sx +lw ,y ,vw ,34 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus2 else (70 ,70 ,80 ),plus_rect2 ,border_radius =4 )
        if hover_minus2 :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect2 ,2 ,border_radius =4 )
        if hover_plus2 :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect2 ,2 ,border_radius =4 )
        minus =self .font_tiny .render ("-",True ,WHITE )
        plus =self .font_tiny .render ("+",True ,WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(sx +lw //2 ,y +17 )))
        self .screen .blit (plus ,plus .get_rect (center =(sx +lw +vw +rw //2 ,y +17 )))
        l_surf =self .font_tiny .render (str (self .initial_level +1 ),True ,WHITE )
        self .screen .blit (l_surf ,l_surf .get_rect (center =(sx +lw +vw //2 ,y +17 )))
        prog =self .story_progress .get (self .config_story_operation ,0 )
        max_start =max (0 ,prog -1 )
        prog_surf =self .font_tiny .render (f"(max {max (1 ,prog )})",True ,GRAY )
        self .screen .blit (prog_surf ,prog_surf .get_rect (midleft =(sx +lw +vw +rw +10 ,y +17 )))

        # Operazione
        y =340 
        label_o =self .font_tiny .render ("Operazione",True ,WHITE )
        rect =label_o .get_rect (midleft =(80 ,y +17 ))
        self .screen .blit (label_o ,rect )
        ops_list =[("moltiplicazione","Moltiplicazione"),("addizione","Addizione"),("sottrazione","Sottrazione"),("divisione","Divisione")]
        bx =360 
        self .opzioni_auto_op_buttons =[]
        for op_key ,op_label in ops_list :
            bw =145 
            bh =34 
            btn_rect =pygame .Rect (bx ,y ,bw ,bh )
            selected =self .config_story_operation ==op_key 
            hovered =btn_rect .collidepoint (mx ,my )
            if selected :
                bg_col =(60 ,130 ,200 )
            elif hovered :
                bg_col =(90 ,90 ,100 )
            else :
                bg_col =(70 ,70 ,80 )
            if selected or hovered :
                pygame .draw .rect (self .screen ,GOLD if hovered else (100 ,180 ,255 ),btn_rect ,2 if hovered else 1 ,border_radius =4 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =4 )
            surf =self .font_tiny .render (op_label ,True ,WHITE )
            self .screen .blit (surf ,surf .get_rect (center =btn_rect .center ))
            self .opzioni_auto_op_buttons .append (btn_rect )
            bx +=bw +12 
        if self .options_cursor ==2 :
            ops_keys =["moltiplicazione","addizione","sottrazione","divisione"]
            sel_idx =ops_keys .index (self .config_story_operation )
            focus_rect =self .opzioni_auto_op_buttons [sel_idx ].inflate (4 ,4 )
            pygame .draw .rect (self .screen ,(255 ,255 ,100 ),focus_rect ,3 ,border_radius =6 )

            # CONFERMA
        y_conf =420 
        conf_rect =pygame .Rect (SCREEN_WIDTH //2 -110 ,y_conf ,220 ,46 )
        hover_conf =conf_rect .collidepoint (mx ,my )
        bg_conf =(50 ,140 ,50 )if hover_conf else (40 ,120 ,40 )
        if hover_conf :
            pygame .draw .rect (self .screen ,GOLD ,(SCREEN_WIDTH //2 -112 ,y_conf -2 ,224 ,50 ),3 ,border_radius =8 )
        pygame .draw .rect (self .screen ,bg_conf ,conf_rect ,border_radius =8 )
        conf_txt =self .font_tiny .render ("CONFERMA",True ,WHITE )
        rect_c =conf_txt .get_rect (center =(SCREEN_WIDTH //2 ,y_conf +23 ))
        self .screen .blit (conf_txt ,rect_c )

    def draw_config (self ):
        mx ,my =pygame .mouse .get_pos ()
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self .font_title .render ("OPZIONI - ALLENAMENTO",True ,GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,80 ))
        self .screen .blit (title ,rect )

        ops =["moltiplicazione","addizione","sottrazione","divisione"]
        op_idx =ops .index (self .config_operation )
        addition =self .config_operation =="addizione"
        subtraction =self .config_operation =="sottrazione"
        division =self .config_operation =="divisione"

        def row_y (r ):
            base =[150 ,210 ,290 ,370 ,420 ,470 ,520 ,550 ]
            pools_mode =addition or subtraction or division 
            cell_h ,gap =30 ,6 
            pool_items =10 if pools_mode else 13 
            subrows_pool =(pool_items +4 )//5 
            pool_extra =max (0 ,(subrows_pool -2 ))*(cell_h +gap )
            offset =0 
            if r >=2 :
                offset +=pool_extra 
            if r >=3 :
                offset +=pool_extra 
            return base [r ]+offset 

            # Row 0: Operazione
        row =0 
        y =row_y (row )
        label_op =self .font_tiny .render ("Operazione",True ,WHITE )
        rect =label_op .get_rect (midleft =(80 ,y +17 ))
        self .screen .blit (label_op ,rect )
        opzioni_op =["Moltiplicazione","Addizione","Sottrazione","Divisione"]
        for i ,nome in enumerate (opzioni_op ):
            sx =360 +i *170 
            sel =i ==op_idx 
            btn_rect =pygame .Rect (sx ,y ,158 ,34 )
            hovered =btn_rect .collidepoint (mx ,my )
            bg_col =(100 ,150 ,220 )if sel and hovered else SEL_BLUE if sel else (80 ,80 ,90 )if hovered else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =4 )
            if hovered :
                pygame .draw .rect (self .screen ,GOLD ,btn_rect ,2 ,border_radius =4 )
            txt =self .font_tiny .render (nome ,True ,WHITE )
            rect_t =txt .get_rect (center =(sx +79 ,y +17 ))
            self .screen .blit (txt ,rect_t )

            # Row 1-2: Pool A / Pool B (unified 5-col grid)
        labels =["Operando A","Operando B"]
        pools =[self .config ["pool_a"],self .config ["pool_b"]]
        cols_u =5 
        pools_mode =addition or subtraction or division 
        for ri in range (2 ):
            row =1 +ri 
            y_base =row_y (row )
            label =self .font_tiny .render (labels [ri ],True ,WHITE )
            rect =label .get_rect (midleft =(80 ,y_base +17 ))
            self .screen .blit (label ,rect )

            items =10 if pools_mode else 13 
            subrows =(items +cols_u -1 )//cols_u 
            cell_w ,cell_h =100 ,30 
            gap =6 
            grid_x =360 
            for sr in range (subrows ):
                sy =y_base +sr *(cell_h +gap )
                for c in range (cols_u ):
                    idx =sr *cols_u +c 
                    if idx >=items :
                        break 
                    sx =grid_x +c *(cell_w +gap )
                    if pools_mode :
                        start =idx *10 
                        end =min (start +9 ,99 )
                        selected =any (pools [ri ][start :start +10 ])
                        txt =f"{start }-{end }"
                    else :
                        selected =pools [ri ][idx ]
                        txt =str (idx )
                    cell_rect =pygame .Rect (sx ,sy ,cell_w ,cell_h )
                    hovered_cell =cell_rect .collidepoint (mx ,my )
                    bg_col =(100 ,150 ,220 )if selected and hovered_cell else SEL_BLUE if selected else (80 ,80 ,90 )if hovered_cell else (60 ,60 ,70 )
                    pygame .draw .rect (self .screen ,bg_col ,cell_rect ,border_radius =4 )
                    if hovered_cell :
                        pygame .draw .rect (self .screen ,GOLD ,cell_rect ,2 ,border_radius =4 )
                    t =self .font_tiny .render (txt ,True ,WHITE )
                    rt =t .get_rect (center =(sx +cell_w //2 ,sy +cell_h //2 ))
                    self .screen .blit (t ,rt )

                    # Row 3: Somma massima / Differenza positiva
        row =3 
        y =row_y (row )
        if addition :
            label_s =self .font_tiny .render ("Somma massima",True ,WHITE )
            rect =label_s .get_rect (midleft =(80 ,y +17 ))
            self .screen .blit (label_s ,rect )
            sx =360 
            lw ,vw ,rw =30 ,40 ,30 
            minus_rect =pygame .Rect (sx ,y ,lw ,34 )
            plus_rect =pygame .Rect (sx +lw +vw ,y ,rw ,34 )
            hover_minus =minus_rect .collidepoint (mx ,my )
            hover_plus =plus_rect .collidepoint (mx ,my )
            pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =4 )
            pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(sx +lw ,y ,vw ,34 ))
            pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =4 )
            if hover_minus :
                pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =4 )
            if hover_plus :
                pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =4 )
            minus =self .font_tiny .render ("-",True ,WHITE )
            plus =self .font_tiny .render ("+",True ,WHITE )
            self .screen .blit (minus ,minus .get_rect (center =(sx +lw //2 ,y +17 )))
            self .screen .blit (plus ,plus .get_rect (center =(sx +lw +vw +rw //2 ,y +17 )))
            s_surf =self .font_tiny .render (str (self .config ["somma_massima"]),True ,WHITE )
            self .screen .blit (s_surf ,s_surf .get_rect (center =(sx +lw +vw //2 ,y +17 )))
        elif subtraction :
            label_d =self .font_tiny .render ("Differenza positiva",True ,WHITE )
            rect =label_d .get_rect (midleft =(80 ,y +17 ))
            self .screen .blit (label_d ,rect )
            toggle_rect =pygame .Rect (352 ,y ,186 ,36 )
            hover_toggle =toggle_rect .collidepoint (mx ,my )
            bg_d =(100 ,150 ,220 )if self .config ["differenza_positiva"]and hover_toggle else SEL_BLUE if self .config ["differenza_positiva"]else (80 ,80 ,90 )if hover_toggle else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_d ,toggle_rect ,border_radius =6 )
            if hover_toggle :
                pygame .draw .rect (self .screen ,GOLD ,toggle_rect ,2 ,border_radius =6 )
            dp_txt ="ON"if self .config ["differenza_positiva"]else "OFF"
            dp_val =self .font_tiny .render (dp_txt ,True ,WHITE )
            rect_dv =dp_val .get_rect (center =(445 ,y +18 ))
            self .screen .blit (dp_val ,rect_dv )
        elif division :
            label_r =self .font_tiny .render ("Risultato intero",True ,WHITE )
            rect =label_r .get_rect (midleft =(80 ,y +17 ))
            self .screen .blit (label_r ,rect )
            toggle_rect =pygame .Rect (352 ,y ,186 ,36 )
            hover_toggle =toggle_rect .collidepoint (mx ,my )
            bg_r =(100 ,150 ,220 )if self .config ["risultato_intero"]and hover_toggle else SEL_BLUE if self .config ["risultato_intero"]else (80 ,80 ,90 )if hover_toggle else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_r ,toggle_rect ,border_radius =6 )
            if hover_toggle :
                pygame .draw .rect (self .screen ,GOLD ,toggle_rect ,2 ,border_radius =6 )
            ri_txt ="ON"if self .config ["risultato_intero"]else "OFF"
            ri_val =self .font_tiny .render (ri_txt ,True ,WHITE )
            rect_rv =ri_val .get_rect (center =(445 ,y +18 ))
            self .screen .blit (ri_val ,rect_rv )

            # Row 4: Domande
        row =4 
        y =row_y (row )
        label_q =self .font_tiny .render ("Domande",True ,WHITE )
        rect =label_q .get_rect (midleft =(80 ,y +17 ))
        self .screen .blit (label_q ,rect )
        qx =360 
        lw ,vw ,rw =30 ,40 ,30 
        minus_rect =pygame .Rect (qx ,y ,lw ,34 )
        plus_rect =pygame .Rect (qx +lw +vw ,y ,rw ,34 )
        hover_minus =minus_rect .collidepoint (mx ,my )
        hover_plus =plus_rect .collidepoint (mx ,my )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =4 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(qx +lw ,y ,vw ,34 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =4 )
        if hover_minus :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =4 )
        if hover_plus :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =4 )
        minus =self .font_tiny .render ("-",True ,WHITE )
        plus =self .font_tiny .render ("+",True ,WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(qx +lw //2 ,y +17 )))
        self .screen .blit (plus ,plus .get_rect (center =(qx +lw +vw +rw //2 ,y +17 )))
        q_surf =self .font_tiny .render (str (self .config ["domande"]),True ,WHITE )
        self .screen .blit (q_surf ,q_surf .get_rect (center =(qx +lw +vw //2 ,y +17 )))

        # Row 5: Commutazione
        row =5 
        y =row_y (row )
        swap_locked =subtraction 
        toggle_rect =pygame .Rect (352 ,y ,186 ,36 )
        hover_toggle =toggle_rect .collidepoint (mx ,my )and not swap_locked 
        bg_swap =(100 ,150 ,220 )if (self .config ["swap"]and hover_toggle )else SEL_BLUE if self .config ["swap"]else (80 ,80 ,90 )if hover_toggle else (60 ,60 ,70 )if not swap_locked else (60 ,60 ,70 )
        if swap_locked :
            bg_swap =(60 ,60 ,70 )
        pygame .draw .rect (self .screen ,bg_swap ,toggle_rect ,border_radius =6 )
        if hover_toggle :
            pygame .draw .rect (self .screen ,GOLD ,toggle_rect ,2 ,border_radius =6 )
        sw_txt ="ON"if (self .config ["swap"]or swap_locked )else "OFF"
        swap_label =self .font_tiny .render ("Commuta A/B",True ,WHITE )
        rect_sl =swap_label .get_rect (midleft =(80 ,y +18 ))
        self .screen .blit (swap_label ,rect_sl )
        swap_val =self .font_tiny .render (sw_txt ,True ,WHITE )
        rect_sv =swap_val .get_rect (center =(445 ,y +18 ))
        self .screen .blit (swap_val ,rect_sv )

        # Row 6: Timeout
        row =6 
        y =row_y (row )
        label_t =self .font_tiny .render ("Timeout (secondi)",True ,WHITE )
        rect =label_t .get_rect (midleft =(80 ,y +17 ))
        self .screen .blit (label_t ,rect )
        tx =360 
        lw ,vw ,rw =30 ,40 ,30 
        minus_rect =pygame .Rect (tx ,y ,lw ,34 )
        plus_rect =pygame .Rect (tx +lw +vw ,y ,rw ,34 )
        hover_minus =minus_rect .collidepoint (mx ,my )
        hover_plus =plus_rect .collidepoint (mx ,my )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =4 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(tx +lw ,y ,vw ,34 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =4 )
        if hover_minus :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =4 )
        if hover_plus :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =4 )
        minus =self .font_tiny .render ("-",True ,WHITE )
        plus =self .font_tiny .render ("+",True ,WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(tx +lw //2 ,y +17 )))
        self .screen .blit (plus ,plus .get_rect (center =(tx +lw +vw +rw //2 ,y +17 )))
        t_surf =self .font_tiny .render (str (self .config ["timeout"]),True ,WHITE )
        self .screen .blit (t_surf ,t_surf .get_rect (center =(tx +lw +vw //2 ,y +17 )))

        # Row 7: CONFERMA
        row =7 
        y =row_y (row )
        conf_rect =pygame .Rect (SCREEN_WIDTH //2 -110 ,y ,220 ,46 )
        hover_conf =conf_rect .collidepoint (mx ,my )
        bg_conf =(50 ,140 ,50 )if hover_conf else (40 ,120 ,40 )
        if hover_conf :
            pygame .draw .rect (self .screen ,GOLD ,(SCREEN_WIDTH //2 -112 ,y -2 ,224 ,50 ),3 ,border_radius =8 )
        pygame .draw .rect (self .screen ,bg_conf ,conf_rect ,border_radius =8 )
        start_txt =self .font_tiny .render ("CONFERMA",True ,WHITE )
        rect_s =start_txt .get_rect (center =(SCREEN_WIDTH //2 ,y +23 ))
        self .screen .blit (start_txt ,rect_s )

    def draw_game (self ):
        shake =(0 ,0 )
        boss_shaking =self .boss_active and self .boss_phase =="shake"
        if self .hit_timer >0 or boss_shaking :
            shake =(random .randint (-6 ,6 ),random .randint (-5 ,5 ))
            self .screen .blit (self .game_bg ,shake )
        else :
            self .screen .blit (self .game_bg ,(0 ,0 ))

        if self .character_entry :
            elapsed =pygame .time .get_ticks ()-self .character_entry_start 
            frame_idx =(elapsed //120 )%4 
            data =self .char_data .get (self .config_gender ,self .char_data ["F"])
            char_img =data ["run"][frame_idx ]
            if self .player_in_dir =="dx":
                char_img =pygame .transform .flip (char_img ,True ,False )
            cw ,ch =char_img .get_size ()
            base_y =SCREEN_HEIGHT //2 -ch //2 
            wy =base_y +130 
            self .screen .blit (char_img ,(self .character_entry_x ,wy ))
            if self .story_fade_alpha >0 :
                fade_surf =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
                fade_surf .set_alpha (self .story_fade_alpha )
                fade_surf .fill (self .story_fade_color )
                self .screen .blit (fade_surf ,(0 ,0 ))
            return 

        wx =self .player_stand_x +shake [0 ]
        data =self .char_data .get (self .config_gender ,self .char_data ["F"])
        if self .player_hit :
            char_img =data ["hit"]
        elif (self .question_active and self .input_utente )or self .zap_timer >0 :
            char_img =data ["charge"]
        else :
            frame_idx =(pygame .time .get_ticks ()//400 )%2 
            char_img =data ["idle"][frame_idx ]
        if self .player_flip :
            char_img =pygame .transform .flip (char_img ,True ,False )
        cw ,ch =char_img .get_size ()
        base_y =SCREEN_HEIGHT //2 -ch //2 
        wy =base_y +130 +shake [1 ]
        wy_monster =base_y +170 +35 +self .monster_y_offset 
        self .screen .blit (char_img ,(wx ,wy ))

        if self .question_active and self .input_utente :
            wand_x =wx +cw -30 if self .player_flip else wx +30 
            glow_x ,glow_y =wand_x ,wy +40 
            base_col =(235 ,220 ,255 )if self .config_gender =="F"else (220 ,255 ,220 )
            t =pygame .time .get_ticks ()
            radius =12 +int (4 *abs ((t %600 )/300 -1 ))
            for r in range (radius ,0 ,-3 ):
                alpha =max (0 ,200 -int (200 *(radius -r )/radius ))
                ratio =(radius -r )/radius 
                col =tuple (max (0 ,int (c *(1 -ratio *0.3 )))for c in base_col )
                surf =pygame .Surface ((r *2 ,r *2 ),pygame .SRCALPHA )
                pygame .draw .circle (surf ,(*col ,alpha ),(r ,r ),r )
                self .screen .blit (surf ,(glow_x -r ,glow_y -r ))

        if self .boss_active and self .boss_phase in ("entrance","fight","defeated"):
            boss_img =None 
            if self .boss_phase =="defeated":
                elapsed_def =pygame .time .get_ticks ()-self .boss_defeated_start 
                if elapsed_def <1500 :
                    boss_img =self .boss_defeated_img 
                else :
                    fade_elapsed =elapsed_def -1500 
                    alpha =max (0 ,255 -int (fade_elapsed /1500 *255 ))
                    if alpha >0 :
                        boss_img =self .boss_defeated_img .copy ()
                        boss_img .set_alpha (alpha )
            elif self .boss_hit :
                boss_img =self .boss_hit_img 
            else :
                boss_img =self .boss_frames [self .boss_anim_frame %len (self .boss_frames )]
            if boss_img :
                bw ,bh =boss_img .get_size ()
                boss_draw_x =self .boss_x +shake [0 ]
                boss_draw_y =wy_monster -(bh -215 )+15 
                self .screen .blit (boss_img ,(boss_draw_x ,boss_draw_y ))
        elif self .monster_hit :
            elapsed =pygame .time .get_ticks ()-self .monster_fade_start 
            if elapsed <self .monster_hit_delay :
                self .screen .blit (self .monster_img ,(self .monster_x +shake [0 ],wy_monster ))
            else :
                fade_elapsed =elapsed -self .monster_hit_delay 
                alpha =max (0 ,255 -int (fade_elapsed /500 *255 ))
                if alpha >0 :
                    faded =self .monster_img .copy ()
                    faded .set_alpha (alpha )
                    self .screen .blit (faded ,(self .monster_x +shake [0 ],wy_monster ))
        else :
            n_frames =len (self .monster_frames )
            self .monster_anim_frame =(pygame .time .get_ticks ()//self .monster_anim_speed )%n_frames 
            self .screen .blit (self .monster_frames [self .monster_anim_frame ],(self .monster_x +shake [0 ],wy_monster ))

        if self .zap_timer >0 :
            start_x ,start_y =(wx +cw -30 )if self .player_flip else (wx +30 ),wy +40 
            if self .zap_reverse :
                end_x ,end_y =wx +cw //2 ,wy +ch //2 
            elif self .boss_active and self .boss_phase in ("entrance","fight","defeated"):
                bw =self .boss_hit_img .get_width ()if self .boss_hit_img else 200 
                bh =self .boss_hit_img .get_height ()if self .boss_hit_img else 200 
                boss_draw_y =wy_monster -(bh -215 )+15 
                end_x ,end_y =self .boss_x +bw //2 ,boss_draw_y +bh //2 
            else :
                end_x ,end_y =self .monster_x +100 ,wy_monster +self .char_h //2 
            mid_x =(start_x +end_x )//2 
            segments =8 
            for offset in range (-4 ,5 ,2 ):
                points =[(start_x ,start_y )]
                for i in range (1 ,segments ):
                    t =i /segments 
                    x =start_x +(end_x -start_x )*t +random .randint (-30 ,30 )
                    y =start_y +(end_y -start_y )*t +random .randint (-40 ,40 )+offset *3 
                    points .append ((x ,y ))
                points .append ((end_x ,end_y ))
                width =3 if abs (offset )<=2 else 1 
                alpha =max (100 ,255 -abs (offset )*40 )
                col =(255 ,255 ,int (255 *self .zap_timer /12 ))if abs (offset )<=2 else (100 ,100 ,255 )
                pygame .draw .lines (self .screen ,col ,False ,points ,width )

        segno =get_operation_symbol (self .operation if hasattr (self ,'operation')else None )
        domanda_text =f"{self .a }  {segno }  {self .b }  =  ?"
        ombra =self .font_large .render (domanda_text ,True ,(30 ,30 ,30 ))
        domanda =self .font_large .render (domanda_text ,True ,WHITE )
        rect =domanda .get_rect (center =(SCREEN_WIDTH //2 ,80 ))
        self .screen .blit (ombra ,(rect .x +2 ,rect .y +2 ))
        self .screen .blit (domanda ,rect )

        if self .question_active :
            text_input =self .input_utente +("|"if pygame .time .get_ticks ()%1000 <500 else " ")
            input_surf =self .font_input .render (text_input ,True ,WHITE )
            input_rect =input_surf .get_rect (center =(SCREEN_WIDTH //2 ,155 ))
            box_rect =input_rect .inflate (40 ,16 )
            box_rect .width =max (box_rect .width ,120 )
            pygame .draw .rect (self .screen ,(40 ,40 ,60 ),box_rect ,border_radius =8 )
            pygame .draw .rect (self .screen ,(100 ,100 ,180 ),box_rect ,2 ,border_radius =8 )
            ombra =self .font_input .render (text_input ,True ,(30 ,30 ,30 ))
            self .screen .blit (ombra ,(input_rect .x +2 ,input_rect .y +2 ))
            self .screen .blit (input_surf ,input_rect )

        if self .mode =="auto":
            richieste =5 +sum (range (1 ,self .level +1 ))
            corr =sum (1 for esito ,_ in self .current_block if esito )
            self .draw_text_shadow (self .font_small ,f"Livello {self .effective_level ()+1 }/{len (self .levels )}",WHITE ,(20 ,20 ))
            mode_txt ="Storia"
        else :
            self .draw_text_shadow (self .font_small ,f"Domanda {self .questions_asked }/{self .total_questions }",WHITE ,(20 ,20 ))
            mode_txt ="Allenamento"
        mode =self .font_small .render (mode_txt ,True ,GRAY )
        rect_m =mode .get_rect (midright =(SCREEN_WIDTH -20 ,20 ))
        self .screen .blit (mode ,rect_m )

        for i in range (WIZARD_LIVES ):
            cx =SCREEN_WIDTH -70 -i *50 
            img =self .heart_red if i <self .lives else self .heart_grey 
            self .screen .blit (img ,(cx -17 ,30 ))

        if self .question_active :
            bar_w =400 
            bar_h =16 
            bar_x =(SCREEN_WIDTH -bar_w )//2 
            bar_y =SCREEN_HEIGHT -45 
            pygame .draw .rect (self .screen ,(60 ,60 ,80 ),(bar_x ,bar_y ,bar_w ,bar_h ),border_radius =8 )
            timer_progresso =self .boss_progress if (self .boss_active and self .boss_phase =="fight")else self .monster_progress 
            rimanente =1.0 -timer_progresso 
            if rimanente >0.4 :
                col_bar =(0 ,200 ,80 )
            elif rimanente >0.2 :
                col_bar =(220 ,200 ,0 )
            else :
                col_bar =(220 ,50 ,50 )
            if rimanente >0 :
                w =int (bar_w *rimanente )
                if w >0 :
                    pygame .draw .rect (self .screen ,col_bar ,(bar_x ,bar_y ,w ,bar_h ),border_radius =8 )

            time_text =self .font_small .render (f"{self .timeout_limit *(1 -timer_progresso ):.0f}s",True ,WHITE )
            rect =time_text .get_rect (midleft =(bar_x +bar_w +15 ,bar_y +bar_h //2 ))
            ombra_t =self .font_small .render (f"{self .timeout_limit *(1 -timer_progresso ):.0f}s",True ,(30 ,30 ,30 ))
            self .screen .blit (ombra_t ,(rect .x +2 ,rect .y +2 ))
            self .screen .blit (time_text ,rect )

        if not self .question_active and self .feedback is not None :
            overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
            overlay .set_alpha (80 )
            overlay .fill (BLACK )
            self .screen .blit (overlay ,(0 ,0 ))

            if self .feedback :
                fb =self .font_large .render ("CORRETTO!",True ,GREEN )
                prossimo =self .font_small .render ("Prossima domanda...",True ,GRAY )
            else :
                fb =self .font_large .render (f"SBAGLIATO! Era {self .expected_result }",True ,RED )
                prossimo =self .font_small .render ("",True ,GRAY )
            rect =fb .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT //2 -30 ))
            ombra_fb =self .font_large .render ("CORRETTO!"if self .feedback else f"SBAGLIATO! Era {self .expected_result }",True ,(30 ,30 ,30 ))
            self .screen .blit (ombra_fb ,(rect .x +2 ,rect .y +2 ))
            self .screen .blit (fb ,rect )
            rect =prossimo .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT //2 +30 ))
            self .screen .blit (prossimo ,rect )

        if self .monster_hit :
            elapsed =pygame .time .get_ticks ()-self .monster_fade_start 
            white_alpha =max (0 ,150 -int (elapsed /200 *150 ))
            if white_alpha >0 :
                flash =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
                flash .set_alpha (white_alpha )
                flash .fill (WHITE )
                self .screen .blit (flash ,(0 ,0 ))

        if self .hit_timer >0 :
            alpha =int (120 *self .hit_timer /12 )
            flash =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
            flash .set_alpha (alpha )
            flash .fill (RED )
            self .screen .blit (flash ,(0 ,0 ))

        if self .heart_reward_active :
            elapsed =pygame .time .get_ticks ()-self .heart_reward_start 
            duration =800 
            if elapsed <duration :
                progress =elapsed /duration 
                alpha =int (255 *min (1.0 ,progress *4 )*max (0 ,1.0 -progress ))
                rise =int (120 *progress )
                heart_img =self .heart_red .copy ()
                heart_img .set_alpha (alpha )
                hx =self .monster_x +65 
                hy =wy_monster -rise 
                self .screen .blit (heart_img ,(hx ,hy ))
            else :
                self .heart_reward_active =False 

        if self .debug :
            label =self .font_stats .render ("DEBUG ON",True ,(0 ,255 ,255 ))
            rect =label .get_rect (bottomright =(SCREEN_WIDTH -15 ,SCREEN_HEIGHT -15 ))
            bg_l =rect .inflate (8 ,4 )
            pygame .draw .rect (self .screen ,(10 ,10 ,20 ),bg_l )
            pygame .draw .rect (self .screen ,(0 ,255 ,255 ),bg_l ,1 )
            self .screen .blit (label ,rect )
            dx ,dy =20 ,80 
            segno_debug =get_operation_symbol (self .operation )
            lines =[
            "DEBUG",
            f"Modalita: {'Storia'if self .mode =='auto'else 'Allenamento'}",
            f"Domanda attiva: {self .question_active }",
            f"Feedback: {self .feedback }",
            f"Game over: {self .game_over }",
            f"Lives: {self .lives }",
            f"Domande: {self .questions_asked }/{self .total_questions if self .mode =='fixed'else self .questions_per_level }",
            f"Tempo medio: {sum (self .answer_times )/len (self .answer_times ):.1f}s"if self .answer_times else "Tempo medio: --",
            f"Timeout: {self .timeout_limit }s"+(f" (iniziale {self .initial_timeout_limit }s)"if self .mode =='auto'else ""),
            f"Livello: {self .effective_level ()+1 }/{len (self .levels )}"if self .mode =='auto'else "Livello: -",
            f"Operandi: {self .a } {segno_debug } {self .b }",
            f"Prev: {self .prev_a } {segno_debug } {self .prev_b }",
            f"Risultato: {self .expected_result }",
            f"Pool A: {format_pool_compact (self .levels [self .effective_level ()]['pool_a'])if self .mode =='auto'else format_pool_compact (self .pool_a )}",
            f"Pool B: {format_pool_compact (self .levels [self .effective_level ()]['pool_b'])if self .mode =='auto'else format_pool_compact (self .pool_b )}",
            f"Coda rinforzo: {list (self .reinforcement_queue )}",
            f"Progresso mostro: {(self .boss_progress if (self .boss_active and self .boss_phase =='fight')else self .monster_progress ):.2f}"+(f"  Tempo: {(pygame .time .get_ticks ()-self .question_start )/1000 :.1f}s"if self .question_active else ""),
            f"Consecutive: {self .consecutive_correct }",
            f"Boss: {'attivo'if self .boss_active else 'no'}"+(f"  fase: {self .boss_phase }  colpi: {self .boss_questions_asked }/{self .boss_total_questions }"if self .boss_active else ""),
            ]
            bg =pygame .Surface ((380 ,len (lines )*22 +10 ))
            bg .set_alpha (200 )
            bg .fill ((10 ,10 ,20 ))
            self .screen .blit (bg ,(dx -5 ,dy -5 ))
            for line in lines :
                surf =self .font_stats .render (line ,True ,(0 ,255 ,255 ))
                rect =surf .get_rect (topleft =(dx ,dy ))
                self .screen .blit (surf ,rect )
                dy +=22 

    def draw_level_complete (self ):
        self .screen .blit (self .game_bg ,(0 ,0 ))
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        self .draw_text_shadow (self .font_title ,f"LIVELLO {self .effective_level ()+1 } COMPLETATO",GOLD ,center =(SCREEN_WIDTH //2 ,80 ))

        tot =len (self .monster_times )
        correct_count =self .stats .get (self .level ,{}).get ("corrette",0 )
        average =sum (self .monster_times )/tot if tot else 0 
        lines =[
        (f"Domande: {len (self .answer_times )}",WHITE ),
        (f"Corrette: {correct_count }",GREEN ),
        (f"Tempo medio: {average :.1f}s",WHITE ),
        ]
        richieste =5 +self .level 
        recent_times =self .monster_times [-richieste :]
        recent_average =sum (recent_times )/len (recent_times )if recent_times else 0 
        if recent_average <self .timeout_limit /2 and not self .is_last_story_level ():
            lines .append (("Tempo medio eccellente! Timeout ridotto di 1s",YELLOW ))

        y =180 
        for text_value ,colore in lines :
            self .draw_text_shadow (self .font_medium ,text_value ,colore ,center =(SCREEN_WIDTH //2 ,y ))
            y +=46 

        self .draw_text_shadow (self .font_small ,"Premi INVIO per continuare",WHITE ,center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -80 ),offset =1 )

    def draw_story (self ):
        entry =self .story_entries [self .story_idx ]if self .story_idx <len (self .story_entries )else {}
        if self .story_is_level and self .story_phase =="exit":
            bg_surf =self .game_bg 
        else :
            bg_name =entry .get ("bg","game")
            bg_surf =self .backgrounds .get (bg_name ,self .bg )
        self .screen .blit (bg_surf ,(0 ,0 ))
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (180 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        text_value =self .story_text_full [:self .story_characters_shown ]

        lines =text_value .split ("\n")
        x_margine =60 
        y =120 
        for line_text in lines :
            words =line_text .split ()
            if not words :
                y +=46 
                continue 
            line =""
            for word in words :
                test =line +" "+word if line else word 
                if self .story_font .size (test )[0 ]>SCREEN_WIDTH -x_margine *2 :
                    self .draw_text_shadow (self .story_font ,line ,WHITE ,midleft =(x_margine ,y ))
                    y +=46 
                    line =word 
                else :
                    line =test 
            if line :
                self .draw_text_shadow (self .story_font ,line ,WHITE ,midleft =(x_margine ,y ))
                y +=46 

        if self .story_fade_alpha >0 :
            fade_surf =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
            fade_surf .set_alpha (self .story_fade_alpha )
            fade_surf .fill (self .story_fade_color )
            self .screen .blit (fade_surf ,(0 ,0 ))

    def draw_player_exit (self ):
        if self .player_exit_retry :
            self .screen .blit (self .game_bg ,(0 ,0 ))
            overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
            overlay .set_alpha (200 )
            overlay .fill (BG_DARK )
            self .screen .blit (overlay ,(0 ,0 ))
        else :
            self .screen .blit (self .game_bg ,(0 ,0 ))
        elapsed =pygame .time .get_ticks ()-self .player_exit_start 
        progress =min (elapsed /4000 ,1.0 )
        frame_idx =(elapsed //200 )%4 
        data =self .char_data .get (self .config_gender ,self .char_data ["F"])
        char_img =data ["run"][frame_idx ]
        if self .player_out_dir =="sx":
            char_img =pygame .transform .flip (char_img ,True ,False )
        cw ,ch =char_img .get_size ()
        if self .player_exit_retry :
            start_x =SCREEN_WIDTH //2 -cw //2 
        else :
            start_x =self .player_stand_x 
        if self .player_out_dir =="dx":
            end_x =SCREEN_WIDTH +200 
        else :
            end_x =-200 
        self .player_exit_x =start_x +(end_x -start_x )*progress 
        base_y =SCREEN_HEIGHT //2 -ch //2 
        wy =base_y +130 
        self .screen .blit (char_img ,(self .player_exit_x ,wy ))

    def draw_gameover (self ):
        self .screen .blit (self .game_bg ,(0 ,0 ))
        overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        if self .mode =="auto":
            self .draw_gameover_story ()
        else :
            self .draw_gameover_fixed ()

    def draw_gameover_story (self ):
        if self .lives <=0 or (self .boss_active and self .boss_phase =="fight"):
            self .draw_text_shadow (self .font_title ,"GAME OVER",RED ,center =(SCREEN_WIDTH //2 ,50 ))
        else :
            self .draw_text_shadow (self .font_title ,"PARTITA TERMINATA",GOLD ,center =(SCREEN_WIDTH //2 ,50 ))

        total_correct =sum (v ["corrette"]for v in self .stats .values ())
        total_wrong =sum (v ["sbagliate"]for v in self .stats .values ())
        completato =not (self .lives <=0 or (self .boss_active and self .boss_phase =="fight"))

        lines =[
        (f"Corrette: {total_correct }",GREEN ),
        (f"Sbagliate: {total_wrong }",RED ),
        (f"Livello raggiunto: {self .effective_level ()+1 }/{len (self .levels )}",WHITE ),
        ]
        if not completato :
            average_monster_time =sum (self .monster_times )/len (self .monster_times )if self .monster_times else 0 
            lines .append ((f"Tempo medio: {average_monster_time :.1f}s",WHITE ))
        y =110 
        for text_value ,colore in lines :
            self .draw_text_shadow (self .font_medium ,text_value ,colore ,center =(SCREEN_WIDTH //2 ,y ))
            y +=46 

        data =self .char_data .get (self .config_gender ,self .char_data ["F"])
        char_img =data ["hit"]if (self .lives <=0 or (self .boss_active and self .boss_phase =="fight"))else data ["idle"][0 ]
        char_x =SCREEN_WIDTH //2 -char_img .get_width ()//2 
        char_y =y +20 
        self .screen .blit (char_img ,(char_x ,char_y ))

        if self .lives <=0 or (self .boss_active and self .boss_phase =="fight"):
            text_value =f"{self .current_profile } si è impegnat-o-a- parecchio, ma gli Hop diventano man mano più impegnativi. Serve più allenamento!"
            m =self .config_gender =="M"
            text_value =re .sub (r'-([^-]+)-([^-]+)-',lambda g :g .group (1 )if m else g .group (2 ),text_value )
        else :
            text_value =f"Complimenti {self .current_profile }! Hai completato tutti i livelli!"
        lines =[]
        max_w =SCREEN_WIDTH -120 
        for word in text_value .split ():
            if not lines :
                lines .append (word )
            else :
                test =lines [-1 ]+" "+word 
                if self .font_small .size (test )[0 ]>max_w :
                    lines .append (word )
                else :
                    lines [-1 ]=test 

        y_text =char_y +char_img .get_height ()+20 
        for line in lines :
            self .draw_text_shadow (self .font_small ,line ,WHITE ,center =(SCREEN_WIDTH //2 ,y_text ))
            y_text +=35 

        mx ,my =pygame .mouse .get_pos ()
        y_btn =y_text +20 
        self .gameover_buttons ={}
        completato =not (self .lives <=0 or (self .boss_active and self .boss_phase =="fight"))
        btns =[("MENU PRINCIPALE","menu")]if completato else [("RIPROVA","restart"),("MENU PRINCIPALE","menu")]
        btn_w =180 
        total_w =len (btns )*btn_w +(len (btns )-1 )*30 
        start_x =SCREEN_WIDTH //2 -total_w //2 
        for i ,(label ,action )in enumerate (btns ):
            bx =start_x +i *(btn_w +30 )
            btn_rect =pygame .Rect (bx ,y_btn ,btn_w ,36 )
            hovered =btn_rect .collidepoint (mx ,my )
            bg_col =(80 ,90 ,100 )if hovered else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =6 )
            if hovered :
                pygame .draw .rect (self .screen ,GOLD ,btn_rect ,2 ,border_radius =6 )
            self .draw_text_shadow (self .font_small ,label ,WHITE ,center =btn_rect .center )
            self .gameover_buttons [action ]=btn_rect 

    def draw_gameover_fixed (self ):
        if self .lives <=0 :
            self .draw_text_shadow (self .font_title ,"GAME OVER",RED ,center =(SCREEN_WIDTH //2 ,50 ))
        else :
            self .draw_text_shadow (self .font_title ,"PARTITA TERMINATA",GOLD ,center =(SCREEN_WIDTH //2 ,50 ))

        total_correct =sum (v ["corrette"]for v in self .stats .values ())
        total_wrong =sum (v ["sbagliate"]for v in self .stats .values ())
        average_time =sum (self .answer_times )/len (self .answer_times )if self .answer_times else 0 

        lines =[
        (f"Corrette: {total_correct }",GREEN ),
        (f"Sbagliate: {total_wrong }",RED ),
        (f"Vite rimaste: {self .lives }",YELLOW ),
        (f"Tempo medio: {average_time :.1f}s",WHITE ),
        ]
        y =110 
        for text_value ,colore in lines :
            self .draw_text_shadow (self .font_medium ,text_value ,colore ,center =(SCREEN_WIDTH //2 ,y ))
            y +=46 

        sessioni =self .load_sessions ()
        if sessioni :
            y +=14 
            self .draw_text_shadow (self .font_medium ,"Ultime sessioni:",GOLD ,center =(SCREEN_WIDTH //2 ,y ))
            y +=34 
            for s in sessioni :
                self .draw_text_shadow (self .font_tiny ,s ,(180 ,180 ,180 ),center =(SCREEN_WIDTH //2 ,y ))
                y +=24 

        mx ,my =pygame .mouse .get_pos ()
        y =max (y +20 ,SCREEN_HEIGHT -100 )
        self .gameover_buttons ={}
        for i ,(label ,action )in enumerate ([("Ricomincia","restart"),("Menu principale","menu")]):
            bx =SCREEN_WIDTH //2 -100 +i *210 
            btn_rect =pygame .Rect (bx ,y ,180 ,36 )
            hovered =btn_rect .collidepoint (mx ,my )
            bg_col =(80 ,90 ,100 )if hovered else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =6 )
            if hovered :
                pygame .draw .rect (self .screen ,GOLD ,btn_rect ,2 ,border_radius =6 )
            self .draw_text_shadow (self .font_small ,label ,WHITE ,center =btn_rect .center )
            self .gameover_buttons [action ]=btn_rect 

    def save_session (self ):
        total_correct =sum (v ["corrette"]for v in self .stats .values ())
        total_wrong =sum (v ["sbagliate"]for v in self .stats .values ())
        average_time =sum (self .answer_times )/len (self .answer_times )if self .answer_times else 0 
        now =datetime .now ().strftime ("%Y-%m-%d %H:%M")
        if self .mode =="auto":
            line_text =f"{now } | Storia | {self .config_story_operation .capitalize ()} | Corrette: {total_correct } | Sbagliate: {total_wrong } | Livello: {self .effective_level ()+1 }/{len (self .levels )} | Tempo medio: {average_time :.1f}s"
        else :
            op_txt =self .operation .capitalize ()if hasattr (self ,'operation')else "Moltiplicazione"
            pool_a_txt =format_pool_compact (self .pool_a )
            pool_b_txt =format_pool_compact (self .pool_b )
            extra =""
            if self .operation =="sottrazione"and getattr (self ,'differenza_positiva',False ):
                extra =" | Diff. positiva: ON"
            if self .operation =="divisione"and getattr (self ,'risultato_intero',True ):
                extra =" | Ris. intero: ON"
            line_text =f"{now } | Allenamento | {op_txt } | Corrette: {total_correct } | Sbagliate: {total_wrong } | Pool A: [{pool_a_txt }] | Pool B: [{pool_b_txt }] | Domande: {self .questions_asked }/{self .total_questions } | Tempo medio: {average_time :.1f}s{extra }"
        path =self .sessions_path ()
        try :
            with open (path ,"a",encoding ="utf-8")as f :
                f .write (line_text +"\n")
        except OSError as e :
            print (f"Warning: unable to write session file '{path }': {e }")

    def load_sessions (self ):
        path =self .sessions_path ()
        if not os .path .exists (path ):
            return []
        try :
            with open (path ,"r",encoding ="utf-8")as f :
                lines =f .readlines ()
        except OSError as e :
            print (f"Warning: unable to read session file '{path }': {e }")
            return []
        ultime =[r .strip ()for r in lines if r .strip ()]
        return list (reversed (ultime [-6 :]))

    def run (self ):
        while self .running :
            for event in pygame .event .get ():
                if event .type ==pygame .QUIT :
                    self .running =False 
                else :
                    self .handle_input (event )

            self .update ()
            self .draw ()
            self .clock .tick (FPS )

        pygame .quit ()
        sys .exit ()

if __name__ =="__main__":
    g =Game ()
    g .run ()
