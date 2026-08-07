import pygame 
import random 
import sys 
import os 
import json 
import re 
import math 
import webbrowser 
from datetime import datetime 
from collections import deque 
from fractions import Fraction 

def resource_path (relative ):
    return os .path .join (getattr (sys ,'_MEIPASS',os .path .dirname (os .path .abspath (__file__ ))),relative )

def app_base_dir ():
    if getattr (sys ,'frozen',False )and sys .platform =="darwin"and os .path .basename (os .path .dirname (os .path .dirname (sys .executable )))=="Contents":
        return os .path .normpath (os .path .join (os .path .dirname (sys .executable ),"..","..",".."))
    return os .path .dirname (sys .executable )if getattr (sys ,'frozen',False )else os .path .dirname (os .path .abspath (__file__ ))

def data_path (relative ):
    return os .path .join (app_base_dir (),relative )

def resolve_profiles_dir ():
    candidates =[os .path .join (app_base_dir (),"profiles")]
    if getattr (sys ,"frozen",False )and sys .platform =="darwin":
        candidates .append (os .path .join (os .path .expanduser ("~"),"Library","Application Support","MathWizard","profiles"))
    for cand in candidates :
        try :
            os .makedirs (cand ,exist_ok =True )
            if os .access (cand ,os .W_OK ):
                return cand
        except OSError :
            continue
    return candidates [0]

PROFILES_DIR =resolve_profiles_dir ()

WIZARD_LIVES =3 
DEFAULT_TIMEOUT =12 
SCREEN_WIDTH =3840 
SCREEN_HEIGHT =2160 
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
            if img .get_size ()!=scale :
                img =pygame .transform .scale (img ,scale )
        return img 
    except (pygame .error ,OSError )as e :
        print (f"Warning: unable to load image '{path }': {e }")
        return make_placeholder_surface (scale if scale is not None else (100 ,100 ))

def scale_to_fit (img ,box ):
    w ,h =img .get_size ()
    f =min (box [0 ]/w ,box [1 ]/h )
    nw =max (1 ,int (round (w *f )))
    nh =max (1 ,int (round (h *f )))
    return pygame .transform .smoothscale (img ,(nw ,nh ))


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


def format_wrong_entry (a ,b ,operation ,answer ):
    segno =get_operation_symbol (operation )
    if answer is None :
        return f"{a }{segno }{b }=(nessuna risposta)"
    return f"{a }{segno }{b }={answer }"


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
                if not isinstance (LEVELS [op ],list ):
                    continue 
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
        self .fullscreen =True 
        try :
            icon =pygame .image .load (resource_path ("graphics/misc/icon.png"))
            if not (icon .get_flags ()&pygame .SRCALPHA ):
                icon =icon .convert_alpha ()
            pygame .display .set_icon (icon )
        except (pygame .error ,OSError ):
            pass 
        self ._last_windowed =self .compute_windowed_size ()
        if self .fullscreen :
            self ._enter_fullscreen ()
        else :
            self .display =pygame .display .set_mode (self ._last_windowed ,pygame .RESIZABLE )
        self .screen =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        self ._scaled_cache =None 
        self ._overlay =pygame .Surface ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        pygame .display .set_caption ("Math Wizard")
        self .setup_cursor ()
        self .clock =pygame .time .Clock ()
        self .running =True 
        self ._text_cache ={}
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
        self .player_stand_x =225 
        self .monster_type ="walk"
        self .monster_y_offset =0 
        self .debug =False 
        self .debug_buf =""
        self .scene_phase =None 
        self .scene_data =None 
        self .scene_npcs =[]
        self .scene_start =0 
        self .scene_exit_start =0 
        self .scene_dialogue_idx =0 
        self .scene_dialogue_start =0 
        self .scene_on_complete =None 
        self .level_scene_before =None 
        self .level_scene_after =None 

        self .font_title =pygame .font .Font (None ,240 )
        self .font_large =pygame .font .Font (None ,192 )
        self .font_medium =pygame .font .Font (None ,126 )
        self .story_font =pygame .font .Font (None ,144 )
        self .font_small =pygame .font .Font (None ,90 )
        self .font_input =pygame .font .Font (None ,168 )
        self .font_stats =pygame .font .Font (None ,84 )
        self .font_num =pygame .font .Font (None ,108 )
        self .font_tiny =pygame .font .Font (None ,66 )

        self .load_resources ()
        self .setup_profiles ()
        self .reset_game_state ()

    def setup_cursor (self ):
        try :
            import os 
            path =resource_path (os .path .join ("graphics","misc","mouse.cur"))
            if not os .path .exists (path ):
                return 
            surf =pygame .image .load (path )
            if not (surf .get_flags ()&pygame .SRCALPHA ):
                surf =surf .convert_alpha ()
            surf =pygame .transform .scale_by (surf ,2 )
            cursor =pygame .cursors .Cursor ((0 ,0 ),surf )
            pygame .mouse .set_cursor (cursor )
        except (pygame .error ,OSError )as e :
            print (f"Warning: unable to set custom cursor from mouse.cur: {e }")

    def update_char_image (self ):
        data =self .char_data .get (self .config_gender ,self .char_data ["F"])
        self .char_img =data ["idle"][0 ]
        self .char_w ,self .char_h =self .char_img .get_size ()

    def load_resources (self ):
        self .bg =safe_load_image (resource_path ("graphics/backgrounds/village.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))
        self .bg_menu =safe_load_image (resource_path ("graphics/MISC/background_menu.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))
        self .bg_options =safe_load_image (resource_path ("graphics/MISC/background_options.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))

        self .backgrounds ={"village":self .bg }
        self ._bg_files ={}
        self ._bg_names =[]
        bg_dir =resource_path ("graphics/backgrounds")
        if os .path .isdir (bg_dir ):
            for fname in sorted (os .listdir (bg_dir )):
                if fname .lower ().endswith ((".png",".jpg",".bmp")):
                    stem =os .path .splitext (fname )[0 ]
                    self ._bg_files [stem ]=os .path .join (bg_dir ,fname )
                    self ._bg_names .append (stem )
        self .game_bg =self .bg 
        self .story_next_bg =self .bg 

        pw ,ph =900 ,1330 
        target_w =160 
        self .char_data ={}
        for key ,path in [("F",resource_path ("graphics/players/playerf.png")),("M",resource_path ("graphics/players/playerm.png"))]:
            idle_frames =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False ,out_size =(819 ,879 ))
            frame0 =idle_frames [0 ].copy ()
            frame1 =pygame .transform .scale (frame0 ,(frame0 .get_width (),frame0 .get_height ()-2 ))
            self .idle_h =frame0 .get_height ()
            idle_frames =[frame0 ,frame1 ]
            shake_frame =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =1 ,flip_x =False ,scale =False ,out_size =(819 ,879 ))[0 ]
            profile_img =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False ,out_size =(819 ,879 ))[0 ]
            hit_frame =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =3 ,flip_x =False ,scale =False ,out_size =(819 ,879 ))[0 ]
            charge_frame =self .load_spritesheet (path ,160 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =2 ,flip_x =False ,scale =False ,out_size =(819 ,879 ))[0 ]
            self .char_data [key ]={"idle":idle_frames ,"profile":profile_img ,"hit":hit_frame ,"charge":charge_frame ,"shake":shake_frame }
            run_frames =self .load_spritesheet (path ,160 ,4 ,row =0 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False ,out_size =(819 ,879 ))
            self .char_data [key ]["run"]=run_frames 
        self .char_img =self .char_data ["F"]["idle"][0 ]
        self .char_h =self .char_img .get_height ()
        self .char_anim_timer =0 
        self .char_anim_frame =0 

        self .monsters ={}
        placeholder_frame =make_placeholder_surface ((200 ,200 ))
        self .monster_frames =[placeholder_frame ]
        self .monster_hit_img =placeholder_frame 
        self .monster_img =placeholder_frame 
        self .monster_anim_speed =150 
        self .monster_hit_delay =150 
        self .previous_monster =None 

        self .boss_data =None 

        self .heart_red =safe_load_image (resource_path ("graphics/misc/lives.png"),(105 ,105 ))
        self .heart_grey =safe_load_image (resource_path ("graphics/misc/lives_lost.png"),(105 ,105 ))

        self .logo =safe_load_image (resource_path ("graphics/misc/logo.png"),(SCREEN_WIDTH ,SCREEN_HEIGHT ))
        self .gear_img =safe_load_image (resource_path ("graphics/misc/gear.png"),(132 ,132 ))

        self .git_icon =scale_to_fit (safe_load_image (resource_path ("graphics/misc/git.png"),None ),(90 ,90 ))
        self .kofi_icon =scale_to_fit (safe_load_image (resource_path ("graphics/misc/kofi.png"),None ),(90 ,90 ))

    def load_spritesheet (self ,path ,target_w ,frame_count ,row =0 ,rows =1 ,cols =None ,frame_offset =0 ,flip_x =True ,scale =True ,out_size =None ):
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
            if out_size :
                frames .append (pygame .transform .scale (frame ,out_size ))
            elif scale :
                frames .append (pygame .transform .scale (frame ,(target_w ,int (target_w /fw *fh ))))
            else :
                frames .append (frame )
        return frames 

    def _get_bg (self ,name ):
        if not name :
            return self .bg 
        surf =self .backgrounds .get (name )
        if surf is None :
            path =self ._bg_files .get (name )
            if path :
                surf =safe_load_image (path ,(SCREEN_WIDTH ,SCREEN_HEIGHT ))
                self .backgrounds [name ]=surf 
        return surf 

    def _get_boss_data (self ):
        if self .boss_data is not None :
            return self .boss_data 
        boss_path =resource_path ("graphics/monsters/monster99.png")
        if os .path .exists (boss_path ):
            boss_walk =self .load_spritesheet (boss_path ,1170 ,2 ,row =0 ,rows =2 ,cols =2 ,frame_offset =0 ,flip_x =False )
            boss_hit =self .load_spritesheet (boss_path ,1170 ,1 ,row =1 ,rows =2 ,cols =2 ,frame_offset =0 ,flip_x =False )[0 ]
            boss_defeated =self .load_spritesheet (boss_path ,1170 ,1 ,row =1 ,rows =2 ,cols =2 ,frame_offset =1 ,flip_x =False )[0 ]
            self .boss_data ={"walk":boss_walk ,"hit":boss_hit ,"defeated":boss_defeated }
        return self .boss_data 

    def _get_monster (self ,idx ):
        monster =self .monsters .get (idx )
        if monster is not None :
            return monster 
        path =resource_path ("graphics/monsters/monster%d.png"%idx )
        if os .path .exists (path ):
            frames =self .load_spritesheet (path ,600 ,4 ,row =0 ,rows =2 ,cols =4 )
            hit =self .load_spritesheet (path ,600 ,1 ,row =1 ,rows =2 ,cols =4 ,frame_offset =3 )[0 ]
            monster ={"frames":frames ,"hit":hit ,"idx":idx }
        else :
            placeholder =make_placeholder_surface ((200 ,200 ))
            monster ={"frames":[placeholder ],"hit":placeholder ,"idx":idx }
        self .monsters [idx ]=monster 
        return monster 

    def _ensure_monsters (self ,wanted ):
        keep =set (wanted )
        for idx in list (self .monsters .keys ()):
            if idx not in keep :
                del self .monsters [idx ]
        for idx in wanted :
            self ._get_monster (idx )

    def _prune_backgrounds (self ):
        keep ={id (self .bg ),id (self .bg_menu ),id (self .bg_options ),id (self .game_bg ),id (self .story_next_bg )}
        for name in list (self .backgrounds .keys ()):
            if id (self .backgrounds [name ])not in keep :
                del self .backgrounds [name ]

    def compute_windowed_size (self ):
        try :
            sizes =pygame .display .get_desktop_sizes ()
        except (pygame .error ,AttributeError ):
            sizes =[]
        if not sizes :
            return (SCREEN_WIDTH ,SCREEN_HEIGHT )
        dw ,dh =sizes [0 ]
        mw ,mh =int (dw *0.95 ),int (dh *0.95 )
        w =max (640 ,mw )
        h =int (w *SCREEN_HEIGHT /SCREEN_WIDTH )
        if h >mh :
            h =max (480 ,mh )
            w =int (h *SCREEN_WIDTH /SCREEN_HEIGHT )
        return (w ,h )

    def _enter_fullscreen (self ):
        try :
            modes =pygame .display .list_modes ()
        except pygame .error :
            modes =[]
        candidates =[]
        if modes :
            candidates .append (tuple (modes [0 ]))
        candidates .append (self .compute_windowed_size ())
        candidates .append ((SCREEN_WIDTH ,SCREEN_HEIGHT ))
        for size in candidates :
            try :
                self .display =pygame .display .set_mode (size ,pygame .FULLSCREEN |pygame .RESIZABLE )
                return
            except pygame .error :
                continue
        try :
            self .display =pygame .display .set_mode ((SCREEN_WIDTH ,SCREEN_HEIGHT ),pygame .FULLSCREEN )
        except pygame .error :
            pass

    def _apply_display_mode (self ):
        if self .fullscreen :
            if not self .display .get_flags ()&pygame .FULLSCREEN :
                self ._last_windowed =self .display .get_size ()
            self ._enter_fullscreen ()
        else :
            size =getattr (self ,'_last_windowed',None )or self .compute_windowed_size ()
            self .display =pygame .display .set_mode (size ,pygame .RESIZABLE )

    def _resize_display (self ,size ):
        self ._last_windowed =size 
        self .display =pygame .display .set_mode (size ,pygame .RESIZABLE )

    def _fit_rect (self ):
        dw ,dh =self .display .get_size ()
        f =min (dw /SCREEN_WIDTH ,dh /SCREEN_HEIGHT )
        tw =max (1 ,int (round (SCREEN_WIDTH *f )))
        th =max (1 ,int (round (SCREEN_HEIGHT *f )))
        return dw ,dh ,tw ,th ,(dw -tw )//2 ,(dh -th )//2 

    def _scale_to_canvas (self ,x ,y ):
        disp =getattr (self ,'display',None )
        if disp is not None and disp is not self .screen :
            dw ,dh ,tw ,th ,ox ,oy =self ._fit_rect ()
            if tw >0 and th >0 :
                x =max (0 ,x -ox )*SCREEN_WIDTH //tw 
                y =max (0 ,y -oy )*SCREEN_HEIGHT //th 
        return x ,y 

    def _mouse_pos (self ):
        mx ,my =pygame .mouse .get_pos ()
        return self ._scale_to_canvas (mx ,my )

    def setup_profiles (self ):
        os .makedirs (PROFILES_DIR ,exist_ok =True )
        idx_file =os .path .join (PROFILES_DIR ,"profiles.json")
        self .profile_cursor =0 
        self .profile_input =""
        self .profile_input_mode =False 
        self .profile_gender_mode =False 
        self .new_profile_name =""
        self .config_cursor_row =0 
        self .config_cursor_col =0 
        self .config_cursor_subrow =0 
        self .reset_profile_config ()
        self .wrong_questions =[]

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

        self .version ="1.1.5"

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

    def reset_profile_config (self ):
        self .config_gender ="F"
        self .config_story_operation ="moltiplicazione"
        self .config_operation ="moltiplicazione"
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
        self .player_shake =False 
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

        self .scene_phase =None 
        self .scene_data =None 
        self .scene_npcs =[]
        self .scene_start =0 
        self .scene_exit_start =0 
        self .scene_dialogue_idx =0 
        self .scene_dialogue_start =0 
        self .scene_on_complete =None 
        self .level_scene_before =None 
        self .level_scene_after =None 
        self .level_is_scene =False 

        self .menu_cursor =0 
        self .options_cursor =0 
        self .menu_btn_rects =[ ]
        self .menu_profile_rect =None 
        self .menu_exit_rect =None 
        self .options_btn_rects =[ ]
        self .options_back_rect =None 
        self .repo_link_rect =None 

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
        self .scene_phase =None 
        self .scene_data =None 
        self .scene_npcs =[]
        self .scene_on_complete =None 
        self .level_scene_before =None 
        self .level_scene_after =None 
        self .level_is_scene =False 
        self .story_monsters =list (range (1 ,9 ))
        self .story_flying_monsters =[]
        self .story_fade_speed =8 
        self .story_next_bg =self .bg 
        self .story_fade_alpha =0 
        self .story_phase ="show"
        self .story_fade_color =(0 ,0 ,0 )
        self .story_object_img =None 
        self .story_object_alpha =0 
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
            if self ._bg_names :
                bg_name =random .choice (self ._bg_names )
                self .game_bg =self ._get_bg (bg_name )or self .bg 
            else :
                self .game_bg =self .bg 
            self ._prune_backgrounds ()
            self .player_in_dir ="sx"
            self .player_out_dir ="dx"
            self .player_entrance =True 
            self .monster_in_dir ="dx"
            self .player_flip =False 
            self .player_stand_x =225 
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
            training_cfg =LEVELS .get ("training",{}).get (self .config_operation ,{})
            self .training_monsters =training_cfg .get ("monsters",list (range (1 ,9 )))
            self .training_flying_monsters =training_cfg .get ("flying",[])
            self ._ensure_monsters (self .training_monsters )
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
        self .wrong_questions =[]
        self .current_block =[]
        self .timeout_handled =False 
        self .scene_data =None 
        self .scene_phase =None 
        self .scene_npcs =[]
        if self .player_entrance :
            self .character_entry =True 
            self .character_entry_start =pygame .time .get_ticks ()
            start_x =-300 if self .player_in_dir =="sx"else SCREEN_WIDTH +80 
            self .character_entry_x =start_x 
        else :
            if self .level_is_scene :
                if self .level_scene_before :
                    self .start_scene (self .level_scene_before ,"scena_end")
                else :
                    self .end_scena ()
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
        if entry_type in ("livello","scena"):
            self .state ="story"
            self .story_is_level =True 
            self .level_is_scene =(entry_type =="scena")
            if not self .level_is_scene :
                self .story_monsters =entry .get ("monsters",list (range (1 ,9 )))
                self .story_flying_monsters =entry .get ("flying",[])
                self ._ensure_monsters (self .story_monsters )
            bg_name =entry .get ("bg","game")
            self .story_next_bg =self ._get_bg (bg_name )or self .bg 
            self .player_in_dir =entry .get ("player_in","sx")
            self .player_out_dir =entry .get ("player_out","dx")
            self .player_entrance =entry .get ("player_entrance","y")=="y"
            if not self .level_is_scene :
                self .monster_in_dir =entry .get ("monster_in","dx")
            self .player_flip =(self .player_in_dir =="dx")
            self .player_stand_x =(SCREEN_WIDTH -225 -self .char_w )if self .player_flip else 225 
            scenes =entry .get ("scenes",[])
            self .level_scene_before =next ((s for s in scenes if s .get ("when")=="before"),None )
            self .level_scene_after =next ((s for s in scenes if s .get ("when")=="after"),None )

            boss_name =entry .get ("boss")
            if not self .level_is_scene and boss_name and self ._get_boss_data ():
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
                    self .boss_end_x =float (SCREEN_WIDTH -225 -boss_w )
                    self .boss_start_x =float (SCREEN_WIDTH +30 )
                else :
                    self .boss_end_x =225.0 
                    self .boss_start_x =float (-boss_w -90 )
                self .boss_x =self .boss_start_x 
            else :
                self .boss_active =False 

            self .story_text_full =""
            self .story_characters_shown =0 
            self .story_object_img =None 
            self .story_object_alpha =0 
            if self .story_fade_alpha >=255 :
                self .game_bg =self .story_next_bg 
                self ._prune_backgrounds ()
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
            text_bg_name =entry .get ("bg","game")
            self .story_next_bg =self ._get_bg (text_bg_name )or self .bg 
            self .game_bg =self .story_next_bg 
            self ._prune_backgrounds ()
            raw_text =entry .get ("testo","")
            raw_text =raw_text .replace ("NOMEPROFILOINUSO",self .current_profile )
            m =self .config_gender =="M"
            self .story_text_full =re .sub (r'-([^-]+)-([^-]+)-',lambda g :g .group (1 )if m else g .group (2 ),raw_text )
            self .story_characters_shown =0 
            self .story_typing_frame =0 
            obj_file =entry .get ("oggetto")
            self .story_object_img =None 
            self .story_object_alpha =0 
            if obj_file :
                obj_img =safe_load_image (resource_path (os .path .join ("graphics","MISC",obj_file )))
                ow ,oh =obj_img .get_size ()
                if oh >900 :
                    s =900 /oh 
                    obj_img =pygame .transform .scale (obj_img ,(max (1 ,int (ow *s )),900 ))
                self .story_object_img =obj_img 
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

    def load_npc_scene (self ,scene ):
        self .scene_data =scene 
        self .scene_npcs =[]
        npc_dir =resource_path ("graphics/npcs")
        ref_h =self .char_h if hasattr (self ,"char_h")and self .char_h else 293 
        def fit (frames ):
            out =[]
            for f in frames :
                if f .get_height ()==ref_h :
                    out .append (f )
                else :
                    w =max (1 ,int (f .get_width ()*ref_h /f .get_height ()))
                    out .append (pygame .transform .scale (f ,(w ,ref_h )))
            return out 
        for i ,n in enumerate (scene .get ("npcs",[])):
            sheet_name =n .get ("sheet")
            if sheet_name :
                sheet_path =os .path .join (npc_dir ,sheet_name if sheet_name .lower ().endswith (".png")else sheet_name +".png")
                walk =fit (self .load_spritesheet (sheet_path ,200 ,4 ,row =0 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False ))
                poses =fit (self .load_spritesheet (sheet_path ,200 ,4 ,row =1 ,rows =2 ,cols =4 ,frame_offset =0 ,flip_x =False ,scale =False ))
            else :
                poses =fit ([safe_load_image (os .path .join (npc_dir ,fname ))for fname in n .get ("frames",[])])
                walk =poses [:4 ]if len (poses )>=4 else poses 
            if not poses :
                continue 
            frame0 =poses [0 ]
            pos =n .get ("pos","left")
            if isinstance (pos ,str ):
                if pos =="center":
                    end_x =float (SCREEN_WIDTH //2 -frame0 .get_width ()//2 )
                elif pos =="right":
                    end_x =float (SCREEN_WIDTH -225 -frame0 .get_width ())
                else :
                    end_x =225.0 
            else :
                end_x =float (pos )
            direzione =n .get ("in","sx")
            if direzione =="dx":
                start_x =float (SCREEN_WIDTH +80 )
            else :
                start_x =float (-frame0 .get_width ()-240 )
            out_side =n .get ("out")
            has_out =out_side is not None 
            if out_side is None :
                out_side ="dx"if direzione =="sx"else "sx"
            flip_in =direzione =="dx"
            flip_out =out_side =="sx"
            if direzione ==out_side :
                flip_out =not flip_in 
            if out_side =="sx":
                exit_x =float (-frame0 .get_width ()-240 )
            else :
                exit_x =float (SCREEN_WIDTH +80 )
            self .scene_npcs .append ({
            "id":n .get ("id",f"npc{i }"),
            "walk":walk ,
            "poses":poses ,
            "poses_idle":[pygame .transform .scale (f ,(max (1 ,f .get_width ()),max (1 ,f .get_height ()-2 )))for f in poses ],
            "pose_idx":0 ,
            "walk_idx":0 ,
            "x":start_x ,
            "start_x":start_x ,
            "end_x":end_x ,
            "has_out":has_out ,
            "exit_x":exit_x ,
            "flip_in":flip_in ,
            "flip_out":flip_out ,
            "y_off":n .get ("y_off",0 ),
            "offset":i *1200 ,
            })

    def npc_idle_frame (self ,npc ,now =None ):
        now =now if now is not None else pygame .time .get_ticks ()
        frame_idx =(now //400 )%2 
        return npc ["poses_idle" if frame_idx else "poses"][npc ["pose_idx"]]

    def start_scene (self ,scene ,on_complete ):
        self .load_npc_scene (scene )
        self .scene_phase ="enter"
        self .scene_start =pygame .time .get_ticks ()
        self .scene_dialogue_idx =0 
        self .scene_dialogue_start =0 
        self .scene_on_complete =on_complete 

    def finish_scene (self ):
        self .scene_data =None 
        self .scene_phase =None 
        self .scene_npcs =[n for n in self .scene_npcs if not n ["has_out"]]
        on_complete =self .scene_on_complete 
        self .scene_on_complete =None 
        if on_complete =="question":
            self .new_question ()
        elif on_complete =="level_complete":
            self .save_session ()
            self .state ="level_complete"
        elif on_complete =="scena_end":
            self .end_scena ()

    def end_scena (self ):
        if self .player_out_dir in ("sx","dx"):
            self .return_to_game =True 
            self .player_exit_start =pygame .time .get_ticks ()
            self .player_exit_x =225 
            self .state ="player_exit"
        else :
            self .story_idx +=1 
            self .show_story ()

    def scene_chars_shown (self ):
        if self .scene_dialogue_start ==0 :
            return 0 
        return (pygame .time .get_ticks ()-self .scene_dialogue_start )//40 

    def resolve_scene_speaker (self ,who ):
        if who in ("player","io")or who ==-1 :
            return ("player",None )
        if isinstance (who ,int )and 0 <=who <len (self .scene_npcs ):
            return ("npc",self .scene_npcs [who ])
        if isinstance (who ,str ):
            for n in self .scene_npcs :
                if n ["id"]==who :
                    return ("npc",n )
        return ("missing",None )

    def set_scene_dialogue (self ,idx ):
        self .scene_dialogue_idx =idx 
        self .scene_dialogue_start =pygame .time .get_ticks ()
        dialogues =self .scene_data .get ("dialogues",[])if self .scene_data else []
        if idx <len (dialogues ):
            n =dialogues [idx ]
            who =n .get ("who",0 )
            kind ,speaker =self .resolve_scene_speaker (who )
            if kind =="npc"and speaker :
                pose =n .get ("frame",speaker ["pose_idx"])
                pose =max (0 ,min (len (speaker ["poses"])-1 ,int (pose )))
                speaker ["pose_idx"]=pose

    def advance_scene_dialogue (self ):
        dialogues =self .scene_data .get ("dialogues",[])if self .scene_data else []
        if self .scene_dialogue_idx >=len (dialogues ):
            return 
        text_value =self .scene_dialogue_text (dialogues [self .scene_dialogue_idx ])
        if self .scene_chars_shown ()<len (text_value ):
            self .scene_dialogue_start =pygame .time .get_ticks ()-(len (text_value )*40 )
            return 
        if self .scene_dialogue_idx +1 >=len (dialogues ):
            if any (npc ["has_out"]for npc in self .scene_npcs ):
                self .scene_phase ="exit"
                self .scene_exit_start =pygame .time .get_ticks ()
            else :
                self .finish_scene ()
        else :
            self .set_scene_dialogue (self .scene_dialogue_idx +1 )

    def scene_dialogue_text (self ,line ):
        text_value =line .get ("text","")
        text_value =text_value .replace ("NOMEPROFILOINUSO",self .current_profile )
        m =self .config_gender =="M"
        return re .sub (r'-([^-]+)-([^-]+)-',lambda g :g .group (1 )if m else g .group (2 ),text_value )

    def draw_speech_bubble (self ):
        dialogues =self .scene_data .get ("dialogues",[])if self .scene_data else []
        if self .scene_dialogue_idx >=len (dialogues ):
            return 
        line =dialogues [self .scene_dialogue_idx ]
        who =line .get ("who",0 )
        kind ,speaker =self .resolve_scene_speaker (who )
        if kind =="player":
            img =self .char_data .get (self .config_gender ,self .char_data ["F"])["idle"][0 ]
            img_w ,img_h =img .get_size ()
            nx =self .player_stand_x
            ny =SCREEN_HEIGHT //2 -img_h //2 +390
        elif kind =="npc"and speaker :
            frame =speaker ["poses"][speaker ["pose_idx"]]
            img_w ,img_h =frame .get_size ()
            nx =speaker ["x"]
            ny =SCREEN_HEIGHT //2 -img_h //2 +390 +speaker ["y_off"]
        else :
            return 
        text_value =self .scene_dialogue_text (line )
        shown =text_value [:self .scene_chars_shown ()]
        font =self .font_small 
        max_w =1560 
        lines =[]
        for para in shown .split ("\n"):
            words =para .split ()
            if not words :
                lines .append ("")
                continue 
            cur =""
            for w in words :
                t =cur +" "+w if cur else w 
                if font .size (t )[0 ]>max_w :
                    lines .append (cur )
                    cur =w 
                else :
                    cur =t 
            lines .append (cur )
        bubble_w =max_w +120 
        line_h =font .get_height ()+18 
        bubble_h =max (132 ,len (lines )*line_h +66 )
        bubble_x =int (nx +img_w //2 -bubble_w //2 )
        bubble_x =max (30 ,min (SCREEN_WIDTH -bubble_w -30 ,bubble_x ))
        bubble_y =int (ny -bubble_h -42 )
        tail_x =int (nx +img_w //2 -bubble_x )
        surf_h =bubble_h +54 
        bubble_surf =pygame .Surface ((bubble_w ,surf_h ),pygame .SRCALPHA )
        pygame .draw .rect (bubble_surf ,(255 ,255 ,255 ,240 ),(0 ,0 ,bubble_w ,bubble_h ),border_radius =42 )
        pygame .draw .polygon (bubble_surf ,(255 ,255 ,255 ,240 ),[(tail_x -42 ,bubble_h ),(tail_x +42 ,bubble_h ),(tail_x ,bubble_h +54 )])
        self .screen .blit (bubble_surf ,(bubble_x ,bubble_y ))
        y =bubble_y +42 
        for ln in lines :
            surf =font .render (ln ,True ,(20 ,20 ,35 ))
            self .screen .blit (surf ,(bubble_x +60 ,y ))
            y +=line_h 
        if self .scene_chars_shown ()>=len (text_value ):
            self .draw_text_shadow (self .font_small ,"Premi INVIO per continuare",WHITE ,center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -120 ),offset =1 )

    def _new_distinct_pair (self ):
        prev =(self .prev_a ,self .prev_b )
        a ,b =None ,None 
        if self .mode =="auto":
            lv =self .effective_level ()
            lv_data =self .levels [lv ]
            for _ in range (20 ):
                a ,b =select_operands (lv_data ["pool_a"],lv_data ["pool_b"],deque (),self .operation ,self .integer_result )
                if (a ,b )!=prev :
                    return a ,b 
        else :
            for _ in range (20 ):
                a ,b =select_operands (self .pool_a ,self .pool_b ,deque (),self .operation ,self .integer_result ,self .max_sum )
                if (a ,b )!=prev :
                    return a ,b 
        return a ,b 

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
                if self .operation =="divisione":
                    self .a ,self .b =self ._new_distinct_pair ()
                else :
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
                if self .mode =="auto"and self .level_scene_after :
                    self .start_scene (self .level_scene_after ,"level_complete")
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
                self .player_exit_x =225 
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
            if self .operation =="divisione":
                self .a ,self .b =self ._new_distinct_pair ()
            elif self .a ==self .b :
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
            wanted =self .story_monsters 
        else :
            wanted =self .training_monsters 
        for idx in wanted :
            self ._get_monster (idx )
        mostri_disponibili =[self .monsters [idx ]for idx in wanted if idx in self .monsters ]
        if not mostri_disponibili :
            self ._get_monster (1 )
            mostri_disponibili =[self .monsters [1 ]]
        scelto =random .choice ([m for m in mostri_disponibili if m is not self .previous_monster ])if len (mostri_disponibili )>1 else mostri_disponibili [0 ]
        self .previous_monster =scelto 
        self .monster_type ="fly"if scelto ["idx"]in (self .story_flying_monsters if self .mode =="auto"else self .training_flying_monsters )else "walk"
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
            self .monster_start_x =-390 
        self .monster_end_x =(self .player_stand_x -375 )if self .monster_in_dir =="sx"else 675 
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
            self ._apply_display_mode ()
            self .setup_cursor ()
            return 
        if event .type ==pygame .VIDEORESIZE and not self .fullscreen :
            self ._resize_display ((event .w ,event .h ))
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
                            self .reset_profile_config ()
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
                            self .reset_profile_config ()
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
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 ))
                        self .initial_level =min (prog_max ,self .initial_level +1 )
                    else :
                        ops =["moltiplicazione","addizione","sottrazione","divisione"]
                        idx =(ops .index (self .config_story_operation )+1 )%4 
                        self .config_story_operation =ops [idx ]
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 ))
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
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 ))
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
                if self .scene_phase =="dialogue":
                    if event .key in (pygame .K_RETURN ,pygame .K_KP_ENTER ,pygame .K_SPACE ):
                        self .advance_scene_dialogue ()
                    elif event .key ==pygame .K_ESCAPE :
                        self .state ="menu"
                    return 
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
                            self .initial_level =self .level 
                            self .save_profile_config ()
                        if average <self .timeout_limit /2 :
                            self .timeout_limit =max (3 ,self .timeout_limit -1 )
                    self .return_to_game =True 
                    self .player_exit_start =pygame .time .get_ticks ()
                    self .player_exit_x =225 
                    self .state ="player_exit"
            elif self .state =="story":
                if event .key in (pygame .K_RETURN ,pygame .K_KP_ENTER ,pygame .K_SPACE ):
                    if self .story_phase =="show":
                        if self .story_characters_shown <len (self .story_text_full ):
                            self .story_characters_shown =len (self .story_text_full )
                        elif self .story_object_img is not None and self .story_object_alpha ==0 :
                            self .story_object_alpha =3 
                        else :
                            self .story_fade_speed =3 
                            self .story_phase ="exit"

        if event .type ==pygame .MOUSEBUTTONDOWN :
            mx ,my =self ._scale_to_canvas (*event .pos ) 
            if self .state =="game"and self .scene_phase =="dialogue":
                self .advance_scene_dialogue ()
                return 
            if self .state =="story":
                if self .story_phase =="show":
                    if self .story_characters_shown <len (self .story_text_full ):
                        self .story_characters_shown =len (self .story_text_full )
                    elif self .story_object_img is not None and self .story_object_alpha ==0 :
                        self .story_object_alpha =3 
                    else :
                        self .story_fade_speed =3 
                        self .story_phase ="exit"
            elif self .state =="gameover":
                if hasattr (self ,'gameover_buttons'):
                    if self .gameover_buttons .get ("restart")and self .gameover_buttons ["restart"].collidepoint (mx ,my ):
                        self .player_exit_retry =True 
                        self .player_exit_start =pygame .time .get_ticks ()
                        self .player_exit_x =225 
                        self .state ="player_exit"
                        return 
                    if self .gameover_buttons .get ("menu")and self .gameover_buttons ["menu"].collidepoint (mx ,my ):
                        self .state ="menu"
                        return 
            if self .state =="menu":
                for i ,hit in enumerate (getattr (self ,'menu_btn_rects',[ ])):
                    if hit .collidepoint (mx ,my ):
                        self .mode ="auto"if i ==0 else "fixed"
                        self .start_game ()
                        return 
                if (mx -3705 )**2 +(my -135 )**2 <=(66 +30 )**2 :
                    self .state ="options"
                    return 
                if getattr (self ,'menu_profile_rect',None )and self .menu_profile_rect .collidepoint (mx ,my ):
                    if self .current_profile in self .profiles :
                        self .profile_cursor =self .profiles .index (self .current_profile )
                    else :
                        self .profile_cursor =0 
                    self .state ="profile_select"
                    return 
                if getattr (self ,'coffee_menu_rect',None )and self .coffee_menu_rect .collidepoint (mx ,my ):
                    try :
                        webbrowser .open ("https://ko-fi.com/thefactor82")
                    except Exception as e :
                        print (f"Warning: unable to open coffee link: {e }")
                if getattr (self ,'menu_exit_rect',None )and self .menu_exit_rect .collidepoint (mx ,my ):
                    self .running =False 
            elif self .state =="profile_select":
                if not self .profile_input_mode :
                    voci =self .profiles +["Nuovo profilo"]
                    for i ,voce in enumerate (voci ):
                        y =510 +i *180 
                        txt =self ._render_cached (self .font_large ,voce ,WHITE )
                        rect =txt .get_rect (midleft =(SCREEN_WIDTH //2 -600 ,y ))
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
                        sx =SCREEN_WIDTH //2 -930 +i *1020 
                        y =1110 
                        prof_img =self .char_data [key ]["profile"]
                        img_w ,img_h =prof_img .get_size ()
                        box_h =max (270 ,img_h +60 )
                        box_rect =pygame .Rect (sx ,y ,840 ,box_h )
                        if box_rect .collidepoint (mx ,my ):
                            self .reset_profile_config ()
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
                for i ,hit in enumerate (getattr (self ,'options_btn_rects',[ ])):
                    if hit .collidepoint (mx ,my ):
                        if i ==0 :
                            self .state ="options_auto"
                        else :
                            self .show_config ()
                        return 
                if getattr (self ,'options_back_rect',None )and self .options_back_rect .collidepoint (mx ,my ):
                    self .state ="menu"
                    return 
                if self .repo_link_rect and self .repo_link_rect .collidepoint (mx ,my ):
                    webbrowser .open ("https://github.com/thefactor82/math-wizard")
                elif getattr (self ,'coffee_options_rect',None )and self .coffee_options_rect .collidepoint (mx ,my ):
                    webbrowser .open ("https://ko-fi.com/thefactor82")
            elif self .state =="options_auto":
                sx =1080 
                lw ,vw ,rw =90 ,120 ,90 
                # Timeout
                if sx -6 <=mx <=sx +lw +vw +rw +6 and 594 <=my <=708 :
                    self .options_cursor =0 
                    if mx <sx +lw :
                        self .auto_timeout =max (3 ,self .auto_timeout -1 )
                    elif mx >=sx +lw +vw :
                        self .auto_timeout =min (99 ,self .auto_timeout +1 )
                    self .save_profile_config ()
                    # Livello iniziale
                elif sx -6 <=mx <=sx +lw +vw +rw +6 and 804 <=my <=918 :
                    self .options_cursor =1 
                    if mx <sx +lw :
                        self .initial_level =max (0 ,self .initial_level -1 )
                    elif mx >=sx +lw +vw :
                        prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 ))
                        self .initial_level =min (prog_max ,self .initial_level +1 )
                    self .save_profile_config ()
                    # Operazione — 4 pulsanti
                if hasattr (self ,'opzioni_auto_op_buttons')and len (self .opzioni_auto_op_buttons )==4 :
                    ops =["moltiplicazione","addizione","sottrazione","divisione"]
                    for i ,btn in enumerate (self .opzioni_auto_op_buttons ):
                        if btn .collidepoint (mx ,my ):
                            self .options_cursor =2 
                            self .config_story_operation =ops [i ]
                            prog_max =max (0 ,self .story_progress .get (self .config_story_operation ,0 ))
                            self .initial_level =min (self .initial_level ,prog_max )
                            self .save_profile_config ()
                            break 
                            # CONFERMA
                if SCREEN_WIDTH //2 -330 <=mx <=SCREEN_WIDTH //2 +330 and 1254 <=my <=1404 :
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
            base =[450 ,630 ,870 ,1110 ,1260 ,1410 ,1560 ,1650 ]
            cell_h ,gap =90 ,18 
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
            mx ,my =self ._scale_to_canvas (*event .pos ) 

            # Row 7: CONFERMA
            y7 =row_y (7 )
            if SCREEN_WIDTH //2 -330 <=mx <=SCREEN_WIDTH //2 +330 and y7 <=my <=y7 +138 :
                self .save_profile_config ()
                self .state ="menu"
                return 

                # Row 0: operation selector
            y0 =row_y (0 )
            if y0 -6 <=my <=y0 +108 :
                for i in range (4 ):
                    sx =1080 +i *510 
                    if sx <=mx <=sx +474 :
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
                cell_w ,cell_h =300 ,90 
                gap =18 
                grid_x =1080 
                for sr in range (subrows ):
                    sy =y_base +sr *(cell_h +gap )
                    for c in range (cols_u ):
                        idx =sr *cols_u +c 
                        if idx >=pool_items :
                            break 
                        sx =grid_x +c *(cell_w +gap )
                        if sx -6 <=mx <=sx +cell_w +6 and sy -6 <=my <=sy +cell_h +6 :
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
            if y3 -6 <=my <=y3 +108 :
                if addition :
                    lw =90 
                    if 1080 -6 <=mx <=1080 +300 +6 :
                        self .config_cursor_row =3 
                        self .config_cursor_col =0 
                        if mx <1080 +lw :
                            self .config ["somma_massima"]=max (1 ,self .config ["somma_massima"]-1 )
                        elif mx >=1080 +lw +120 :
                            self .config ["somma_massima"]=min (199 ,self .config ["somma_massima"]+1 )
                        return 
                elif subtraction :
                    if 1050 <=mx <=1620 and y3 -12 <=my <=y3 +120 :
                        self .config_cursor_row =3 
                        self .config_cursor_col =0 
                        self .config ["differenza_positiva"]=not self .config ["differenza_positiva"]
                        return 
                elif division :
                    if 1050 <=mx <=1620 and y3 -12 <=my <=y3 +120 :
                        self .config_cursor_row =3 
                        self .config_cursor_col =0 
                        self .config ["risultato_intero"]=not self .config ["risultato_intero"]
                        return 

                        # Row 4: domande
            y4 =row_y (4 )
            if y4 -6 <=my <=y4 +108 :
                lw =90 
                if 1080 -6 <=mx <=1080 +300 +6 :
                    self .config_cursor_row =4 
                    self .config_cursor_col =0 
                    if mx <1080 +lw :
                        self .config ["domande"]=max (1 ,self .config ["domande"]-1 )
                    elif mx >=1080 +lw +120 :
                        self .config ["domande"]=min (99 ,self .config ["domande"]+1 )
                    return 

                    # Row 5: swap
            y5 =row_y (5 )
            if y5 -12 <=my <=y5 +120 :
                if 1050 <=mx <=1620 and not subtraction :
                    self .config_cursor_row =5 
                    self .config_cursor_col =0 
                    self .config ["swap"]=not self .config ["swap"]
                    return 

                    # Row 6: timeout
            y6 =row_y (6 )
            if y6 -6 <=my <=y6 +108 :
                lw =90 
                if 1080 -6 <=mx <=1080 +300 +6 :
                    self .config_cursor_row =6 
                    self .config_cursor_col =0 
                    if mx <1080 +lw :
                        self .config ["timeout"]=max (3 ,self .config ["timeout"]-1 )
                    elif mx >=1080 +lw +120 :
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
            self .wrong_questions .append ((self .a ,self .b ,self .operation ,text_value ,self .expected_result ))
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
        self .wrong_questions .append ((self .a ,self .b ,self .operation ,None ,self .expected_result ))
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
                self .logo =None 
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
                    self .player_hit =False 
                    self .hit_timer =0 
                    self .player_shake =False 
                    self .zap_timer =0 
                    self .zap_reverse =False 
                    self .monster_hit =False 
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
                elif self .story_object_img is not None and self .story_object_alpha >0 and self .story_object_alpha <255 :
                    self .story_object_alpha =min (255 ,self .story_object_alpha +3 )
            elif self .story_phase =="exit":
                self .story_fade_alpha =min (255 ,self .story_fade_alpha +self .story_fade_speed )
                if self .story_fade_alpha >=255 :
                    if self .story_is_level :
                        self .game_bg =self .story_next_bg 
                        self ._prune_backgrounds ()
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
                            if skip_to is not None and skip_to >self .story_idx :
                                while skip_to >0 and self .story_entries [skip_to -1 ].get ("tipo")=="scena":
                                    skip_to -=1 
                                self .story_idx =skip_to 
                            else :
                                self .story_idx +=1 
                        else :
                            self .story_idx +=1 
                        self .show_story ()
            return 
        if self .state not in ("game",):
            return 

        if self .scene_phase is not None :
            now =pygame .time .get_ticks ()
            if self .scene_phase =="enter":
                dur =1200 
                max_offset =max ([npc ["offset"]for npc in self .scene_npcs ],default =0 )
                for npc in self .scene_npcs :
                    e =now -self .scene_start -npc ["offset"]
                    if e <=0 :
                        continue 
                    p =min (e /dur ,1.0 )
                    ease =1 -(1 -p )**3 
                    npc ["x"]=npc ["start_x"]+(npc ["end_x"]-npc ["start_x"])*ease 
                if now -self .scene_start >=max_offset +dur :
                    self .scene_phase ="dialogue"
                    self .set_scene_dialogue (0 )
            elif self .scene_phase =="dialogue":
                pass 
            elif self .scene_phase =="exit":
                dur =1200 
                done =True 
                for npc in self .scene_npcs :
                    if not npc ["has_out"]:
                        continue 
                    e =now -self .scene_exit_start 
                    p =min (e /dur ,1.0 )
                    ease =1 -(1 -p )**3 
                    npc ["x"]=npc ["end_x"]+(npc ["exit_x"]-npc ["end_x"])*ease 
                    if p <1.0 :
                        done =False 
                if done :
                    self .finish_scene ()
            return 

        if self .character_entry :
            elapsed =pygame .time .get_ticks ()-self .character_entry_start 
            duration =1200 
            progress =min (elapsed /duration ,1.0 )
            end_x =self .player_stand_x 
            start_x =-300 if self .player_in_dir =="sx"else SCREEN_WIDTH +80 
            self .character_entry_x =start_x +(end_x -start_x )*progress 
            if progress >=1.0 :
                self .character_entry =False 
                if self .level_is_scene :
                    if self .level_scene_before :
                        self .start_scene (self .level_scene_before ,"scena_end")
                    else :
                        self .end_scena ()
                elif self .mode =="auto"and self .level_scene_before :
                    self .start_scene (self .level_scene_before ,"question")
                else :
                    self .new_question ()
            return 

        if self .boss_active and self .boss_phase =="shake":
            elapsed =pygame .time .get_ticks ()-self .boss_shake_start 
            duration =2000 
            self .player_shake =True 
            if elapsed >=duration :
                self .boss_phase ="entrance"
                self .boss_entrance_start =pygame .time .get_ticks ()
            return 

        if self .boss_active and self .boss_phase =="entrance":
            elapsed =pygame .time .get_ticks ()-self .boss_entrance_start 
            duration =2000 
            progress =min (elapsed /duration ,1.0 )
            ease =1 -(1 -progress )**3 
            self .boss_x =self .boss_start_x +(self .boss_end_x -self .boss_start_x )*ease 
            if progress >=1.0 :
                self .boss_phase ="fight"
                self .player_shake =False 
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
                if hit_elapsed >1450 :
                    self .boss_hit =False 
            if self .question_active :
                elapsed =(pygame .time .get_ticks ()-self .question_start -self .boss_paused_ms )/1000.0 
                self .boss_progress =min (elapsed /self .boss_timeout ,1.0 )
                boss_w =self .boss_hit_img .get_width ()
                fight_end =float (self .player_stand_x -boss_w +300 )if self .boss_end_x <self .player_stand_x else float (self .player_stand_x +self .char_w -300 )
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
                    if self .level_scene_after :
                        self .start_scene (self .level_scene_after ,"level_complete")
                        return 
                    self .save_session ()
                    self .state ="level_complete"
            return 

        if self .question_active :
            elapsed =(pygame .time .get_ticks ()-self .question_start )/1000.0 
            self .monster_progress =min (elapsed /self .timeout_limit ,1.0 )
            self .monster_x =self .monster_start_x +(self .monster_end_x -self .monster_start_x )*self .monster_progress 
            if self .monster_type =="fly":
                self .monster_y_offset =90 *math .sin (self .monster_progress *6 *math .pi )
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

        if self .screen is self .display :
            pygame .display .flip ()
            return 
        dw ,dh ,tw ,th ,ox ,oy =self ._fit_rect ()
        if tw ==dw and th ==dh :
            pygame .transform .scale (self .screen ,(tw ,th ),self .display )
        else :
            if self ._scaled_cache is None or self ._scaled_cache .get_size ()!=(tw ,th ):
                self ._scaled_cache =pygame .Surface ((tw ,th ))
            pygame .transform .scale (self .screen ,(tw ,th ),self ._scaled_cache )
            self .display .fill (BLACK )
            self .display .blit (self ._scaled_cache ,(ox ,oy ))
        pygame .display .flip ()

    def _render_cached (self ,font ,text ,color ):
        key =(id (font ),text ,color )
        surf =self ._text_cache .get (key )
        if surf is None :
            if len (self ._text_cache )>2000 :
                self ._text_cache .clear ()
            surf =font .render (text ,True ,color )
            self ._text_cache [key ]=surf 
        return surf 

    def draw_text_shadow (self ,font ,text ,color ,pos =None ,center =None ,midleft =None ,midright =None ,offset =6 ):
        ombra =self ._render_cached (font ,text ,(30 ,30 ,30 ))
        surf =self ._render_cached (font ,text ,color )
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
        if self .logo is None :
            return 
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
        overlay =self ._overlay
        overlay .set_alpha (alpha )
        overlay .fill (BLACK )
        self .screen .blit (overlay ,(0 ,0 ))

    def draw_profile (self ):
        mx ,my =self ._mouse_pos ()
        overlay =self ._overlay
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        if self .profile_input_mode :
            if self .profile_gender_mode :
                title =self ._render_cached (self .font_title ,"NUOVO PROFILO",GOLD )
                rect =title .get_rect (center =(SCREEN_WIDTH //2 ,300 ))
                self .screen .blit (title ,rect )

                nome_label =self ._render_cached (self .font_medium ,f"Profilo: {self .profile_input }",WHITE )
                rect =nome_label .get_rect (center =(SCREEN_WIDTH //2 ,600 ))
                self .screen .blit (nome_label ,rect )

                prompt =self ._render_cached (self .font_large ,"Seleziona il personaggio:",WHITE )
                rect =prompt .get_rect (center =(SCREEN_WIDTH //2 ,900 ))
                self .screen .blit (prompt ,rect )

                for i ,key in enumerate (("F","M")):
                    sx =SCREEN_WIDTH //2 -930 +i *1020 
                    y =1110 
                    prof_img =self .char_data [key ]["profile"]
                    img_w ,img_h =prof_img .get_size ()
                    box_h =max (270 ,img_h +60 )
                    box_rect =pygame .Rect (sx ,y ,840 ,box_h )
                    hovered =box_rect .collidepoint (mx ,my )
                    bg_col =(80 ,80 ,100 )if hovered else (60 ,60 ,70 )
                    pygame .draw .rect (self .screen ,bg_col ,box_rect ,border_radius =24 )
                    if hovered :
                        pygame .draw .rect (self .screen ,GOLD ,box_rect ,2 ,border_radius =24 )
                    if prof_img :
                        cx =sx +(840 -img_w )//2 
                        cy =y +(box_h -img_h )//2 
                        self .screen .blit (prof_img ,(cx ,cy ))

            else :
                title =self ._render_cached (self .font_title ,"NUOVO PROFILO",GOLD )
                rect =title .get_rect (center =(SCREEN_WIDTH //2 ,360 ))
                self .screen .blit (title ,rect )

                lbl =self ._render_cached (self .font_medium ,"Inserisci il nome:",WHITE )
                rect =lbl .get_rect (center =(SCREEN_WIDTH //2 ,780 ))
                self .screen .blit (lbl ,rect )

                txt =self .profile_input +("|"if pygame .time .get_ticks ()%1000 <500 else " ")
                surf =self ._render_cached (self .font_input ,txt ,WHITE )
                box =surf .get_rect (center =(SCREEN_WIDTH //2 ,990 ))
                bg =box .inflate (120 ,48 )
                bg .width =max (bg .width ,600 )
                pygame .draw .rect (self .screen ,(40 ,40 ,60 ),bg ,border_radius =24 )
                pygame .draw .rect (self .screen ,(100 ,100 ,180 ),bg ,2 ,border_radius =24 )
                self .screen .blit (surf ,box )

                if self .profile_input :
                    hint =self ._render_cached (self .font_small ,"",GRAY )
                    rect =hint .get_rect (center =(SCREEN_WIDTH //2 ,1140 ))
                    self .screen .blit (hint ,rect )
                back =self ._render_cached (self .font_small ,"",GRAY )
                rect =back .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -180 ))
                self .screen .blit (back ,rect )
            return 

        title =self ._render_cached (self .font_title ,"SELEZIONA PROFILO",GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,240 ))
        self .screen .blit (title ,rect )

        voci =self .profiles +["Nuovo profilo"]
        nuovo_idx =len (self .profiles )
        for i ,voce in enumerate (voci ):
            y =510 +i *180 
            txt =self ._render_cached (self .font_large ,voce ,WHITE )
            rect =txt .get_rect (midleft =(SCREEN_WIDTH //2 -600 ,y ))
            if rect .collidepoint (mx ,my ):
                self .profile_cursor =i 
                txt =self ._render_cached (self .font_large ,voce ,GOLD )
            self .screen .blit (txt ,rect )
            if i <nuovo_idx and voce ==self .current_profile :
                ok =self ._render_cached (self .font_small ,"(attivo)",GRAY )
                rect =ok .get_rect (midleft =(SCREEN_WIDTH //2 +450 ,y ))
                self .screen .blit (ok ,rect )

    def blit_link_icon (self ,img ,rect ):
        w ,h =img .get_size ()
        self .screen .blit (img ,(rect .x +(rect .w -w )//2 ,rect .y +(rect .h -h )//2 ))

    def draw_menu (self ):
        mx ,my =self ._mouse_pos ()
        overlay =self ._overlay
        overlay .set_alpha (180 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self ._render_cached (self .font_title ,"MATH WIZARD",GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,300 ))
        self .screen .blit (title ,rect )

        subtitle =self ._render_cached (self .font_medium ,"Impara divertendoti!",WHITE )
        rect =subtitle .get_rect (center =(SCREEN_WIDTH //2 ,480 ))
        self .screen .blit (subtitle ,rect )

        opzioni =[
        ("Storia","Affronta un'avventura nel regno di Math, con incremento automatico della difficoltà."),
        ("Allenamento","Scegli le varie impostazioni per una sfida breve a difficoltà costante"),
        ]
        self .menu_btn_rects =[ ]
        for i ,(tit ,desc )in enumerate (opzioni ):
            y =840 +i *300 
            opt =self ._render_cached (self .font_large ,tit ,WHITE )
            rect =opt .get_rect (midleft =(SCREEN_WIDTH //2 -900 ,y ))
            hit =rect .inflate (60 ,30 )
            self .menu_btn_rects .append (hit )
            if hit .collidepoint (mx ,my ):
                self .menu_cursor =i 
                opt =self ._render_cached (self .font_large ,tit ,GOLD )
            self .screen .blit (opt ,rect )
            desc_surf =self ._render_cached (self .font_small ,desc ,GRAY )
            rect =desc_surf .get_rect (midleft =(SCREEN_WIDTH //2 -900 ,y +120 ))
            self .screen .blit (desc_surf ,rect )

            # gear icon
        cx ,cy =SCREEN_WIDTH -135 ,135 
        gear_scaled =self .gear_img 
        rect =gear_scaled .get_rect (center =(cx ,cy ))
        if rect .collidepoint (mx ,my ):
            pygame .draw .rect (self .screen ,GOLD ,rect .inflate (24 ,24 ),2 ,border_radius =18 )
        self .screen .blit (gear_scaled ,rect )

        profile_label =self ._render_cached (self .font_small ,f"Profilo: {self .current_profile }",GRAY )
        rect =profile_label .get_rect (midleft =(SCREEN_WIDTH //2 -900 ,1650 ))
        self .menu_profile_rect =rect .inflate (60 ,30 )
        if self .menu_profile_rect .collidepoint (mx ,my ):
            profile_label =self ._render_cached (self .font_small ,f"Profilo: {self .current_profile }",GOLD )
        self .screen .blit (profile_label ,rect )

        exit_txt =self ._render_cached (self .font_large ,"ESCI",WHITE )
        exit_rect =exit_txt .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -150 ))
        self .menu_exit_rect =exit_rect .inflate (60 ,30 )
        if self .menu_exit_rect .collidepoint (mx ,my ):
            exit_txt =self ._render_cached (self .font_large ,"ESCI",GOLD )
        self .screen .blit (exit_txt ,exit_rect )

        version_surf =self ._render_cached (self .font_tiny ,f"v{self .version }",GRAY )
        rect =version_surf .get_rect (bottomright =(SCREEN_WIDTH -24 ,SCREEN_HEIGHT -24 ))
        self .screen .blit (version_surf ,rect )

        icon_size =90 
        icon_x =48 
        coffee_txt =self ._render_cached (self .font_small ,"Offrimi un caffè",WHITE )
        coffee_rect =coffee_txt .get_rect (bottomleft =(icon_x +icon_size +30 ,SCREEN_HEIGHT -48 ))
        if coffee_rect .collidepoint (mx ,my ):
            coffee_txt =self ._render_cached (self .font_small ,"Offrimi un caffè",GOLD )
            coffee_rect =coffee_txt .get_rect (bottomleft =(icon_x +icon_size +30 ,SCREEN_HEIGHT -48 ))
        coffee_icon_rect =pygame .Rect (icon_x ,coffee_rect .centery -icon_size //2 ,icon_size ,icon_size )
        self .blit_link_icon (self .kofi_icon ,coffee_icon_rect )
        self .screen .blit (coffee_txt ,coffee_rect )
        self .coffee_menu_rect =coffee_rect .union (coffee_icon_rect )

    def draw_options (self ):
        mx ,my =self ._mouse_pos ()
        overlay =self ._overlay
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self ._render_cached (self .font_title ,"OPZIONI",GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,240 ))
        self .screen .blit (title ,rect )

        voci =["Storia","Allenamento"]
        self .options_btn_rects =[ ]
        for i ,voce in enumerate (voci ):
            y =660 +i *240 
            txt =self ._render_cached (self .font_large ,voce ,WHITE )
            rect =txt .get_rect (center =(SCREEN_WIDTH //2 ,y +63 ))
            hit =rect .inflate (60 ,30 )
            self .options_btn_rects .append (hit )
            if hit .collidepoint (mx ,my ):
                self .options_cursor =i 
                txt =self ._render_cached (self .font_large ,voce ,GOLD )
            self .screen .blit (txt ,rect )

        credits =[
        f"v{self .version }",
        "Concept, development, and organization: TheFactor82",
        "Development, Beta testing: SL, GA, WF",
        "Graphics: Elena",
        ]
        y =SCREEN_HEIGHT -234 -len (credits )*66 
        for line in credits :
            surf =self ._render_cached (self .font_tiny ,line ,GRAY )
            rect =surf .get_rect (bottomright =(SCREEN_WIDTH -60 ,y ))
            self .screen .blit (surf ,rect )
            y +=66 

        icon_size =90 
        coffee_txt =self ._render_cached (self .font_small ,"Offrimi un caffè",WHITE )
        coffee_rect =coffee_txt .get_rect (bottomright =(SCREEN_WIDTH -60 ,SCREEN_HEIGHT -144 ))
        if coffee_rect .collidepoint (mx ,my ):
            coffee_txt =self ._render_cached (self .font_small ,"Offrimi un caffè",GOLD )
            coffee_rect =coffee_txt .get_rect (bottomright =(SCREEN_WIDTH -60 ,SCREEN_HEIGHT -144 ))
        coffee_icon_rect =pygame .Rect (coffee_rect .left -24 -icon_size ,coffee_rect .centery -icon_size //2 ,icon_size ,icon_size )
        self .blit_link_icon (self .kofi_icon ,coffee_icon_rect )
        self .screen .blit (coffee_txt ,coffee_rect )
        self .coffee_options_rect =coffee_rect .union (coffee_icon_rect )

        link_txt =self ._render_cached (self .font_small ,"Progetto Github",WHITE )
        link_rect =link_txt .get_rect (bottomright =(SCREEN_WIDTH -60 ,SCREEN_HEIGHT -30 ))
        if link_rect .collidepoint (mx ,my ):
            link_txt =self ._render_cached (self .font_small ,"Progetto Github",GOLD )
            link_rect =link_txt .get_rect (bottomright =(SCREEN_WIDTH -60 ,SCREEN_HEIGHT -30 ))
        link_icon_rect =pygame .Rect (link_rect .left -24 -icon_size ,link_rect .centery -icon_size //2 ,icon_size ,icon_size )
        self .blit_link_icon (self .git_icon ,link_icon_rect )
        self .screen .blit (link_txt ,link_rect )
        self .repo_link_rect =link_rect .union (link_icon_rect )

        back_txt =self ._render_cached (self .font_small ,"Indietro",WHITE )
        back_rect =back_txt .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -60 ))
        self .options_back_rect =back_rect .inflate (60 ,30 )
        if self .options_back_rect .collidepoint (mx ,my ):
            back_txt =self ._render_cached (self .font_small ,"Indietro",GOLD )
        self .screen .blit (back_txt ,back_rect )

    def draw_auto_options (self ):
        mx ,my =self ._mouse_pos ()
        overlay =self ._overlay
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self ._render_cached (self .font_title ,"OPZIONI - STORIA",GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,240 ))
        self .screen .blit (title ,rect )

        # Timeout
        y =600 
        label_t =self ._render_cached (self .font_tiny ,"Timeout (secondi)",WHITE )
        rect =label_t .get_rect (midleft =(240 ,y +51 ))
        self .screen .blit (label_t ,rect )
        focused =self .options_cursor ==0 
        sx =1080 
        lw ,vw ,rw =90 ,120 ,90 
        minus_rect =pygame .Rect (sx ,y ,lw ,102 )
        plus_rect =pygame .Rect (sx +lw +vw ,y ,rw ,102 )
        hover_minus =minus_rect .collidepoint (mx ,my )
        hover_plus =plus_rect .collidepoint (mx ,my )
        if focused :
            pygame .draw .rect (self .screen ,SEL_BLUE ,(sx -6 ,y -6 ,lw +vw +rw +12 ,114 ),0 ,border_radius =12 )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =12 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(sx +lw ,y ,vw ,102 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =12 )
        if hover_minus :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =12 )
        if hover_plus :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =12 )
        minus =self ._render_cached (self .font_tiny ,"-",WHITE )
        plus =self ._render_cached (self .font_tiny ,"+",WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(sx +lw //2 ,y +51 )))
        self .screen .blit (plus ,plus .get_rect (center =(sx +lw +vw +rw //2 ,y +51 )))
        t_surf =self ._render_cached (self .font_tiny ,str (self .auto_timeout ),WHITE )
        self .screen .blit (t_surf ,t_surf .get_rect (center =(sx +lw +vw //2 ,y +51 )))

        # Livello iniziale
        y =810 
        label_l =self ._render_cached (self .font_tiny ,"Livello iniziale",WHITE )
        rect =label_l .get_rect (midleft =(240 ,y +51 ))
        self .screen .blit (label_l ,rect )
        focused =self .options_cursor ==1 
        minus_rect2 =pygame .Rect (sx ,y ,lw ,102 )
        plus_rect2 =pygame .Rect (sx +lw +vw ,y ,rw ,102 )
        hover_minus2 =minus_rect2 .collidepoint (mx ,my )
        hover_plus2 =plus_rect2 .collidepoint (mx ,my )
        if focused :
            pygame .draw .rect (self .screen ,SEL_BLUE ,(sx -6 ,y -6 ,lw +vw +rw +12 ,114 ),0 ,border_radius =12 )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus2 else (70 ,70 ,80 ),minus_rect2 ,border_radius =12 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(sx +lw ,y ,vw ,102 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus2 else (70 ,70 ,80 ),plus_rect2 ,border_radius =12 )
        if hover_minus2 :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect2 ,2 ,border_radius =12 )
        if hover_plus2 :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect2 ,2 ,border_radius =12 )
        minus =self ._render_cached (self .font_tiny ,"-",WHITE )
        plus =self ._render_cached (self .font_tiny ,"+",WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(sx +lw //2 ,y +51 )))
        self .screen .blit (plus ,plus .get_rect (center =(sx +lw +vw +rw //2 ,y +51 )))
        l_surf =self ._render_cached (self .font_tiny ,str (self .initial_level +1 ),WHITE )
        self .screen .blit (l_surf ,l_surf .get_rect (center =(sx +lw +vw //2 ,y +51 )))
        prog =self .story_progress .get (self .config_story_operation ,0 )
        prog_surf =self ._render_cached (self .font_tiny ,f"(max {max (1 ,prog +1 )})",GRAY )
        self .screen .blit (prog_surf ,prog_surf .get_rect (midleft =(sx +lw +vw +rw +30 ,y +51 )))

        # Operazione
        y =1020 
        label_o =self ._render_cached (self .font_tiny ,"Operazione",WHITE )
        rect =label_o .get_rect (midleft =(240 ,y +51 ))
        self .screen .blit (label_o ,rect )
        ops_list =[("moltiplicazione","Moltiplicazione"),("addizione","Addizione"),("sottrazione","Sottrazione"),("divisione","Divisione")]
        bx =1080 
        self .opzioni_auto_op_buttons =[]
        for op_key ,op_label in ops_list :
            bw =435 
            bh =102 
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
                pygame .draw .rect (self .screen ,GOLD if hovered else (100 ,180 ,255 ),btn_rect ,2 if hovered else 1 ,border_radius =12 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =12 )
            surf =self ._render_cached (self .font_tiny ,op_label ,WHITE )
            self .screen .blit (surf ,surf .get_rect (center =btn_rect .center ))
            self .opzioni_auto_op_buttons .append (btn_rect )
            bx +=bw +36 
        if self .options_cursor ==2 :
            ops_keys =["moltiplicazione","addizione","sottrazione","divisione"]
            sel_idx =ops_keys .index (self .config_story_operation )
            focus_rect =self .opzioni_auto_op_buttons [sel_idx ].inflate (12 ,12 )
            pygame .draw .rect (self .screen ,(255 ,255 ,100 ),focus_rect ,3 ,border_radius =18 )

            # CONFERMA
        y_conf =1260 
        conf_rect =pygame .Rect (SCREEN_WIDTH //2 -330 ,y_conf ,660 ,138 )
        hover_conf =conf_rect .collidepoint (mx ,my )
        bg_conf =(50 ,140 ,50 )if hover_conf else (40 ,120 ,40 )
        if hover_conf :
            pygame .draw .rect (self .screen ,GOLD ,(SCREEN_WIDTH //2 -336 ,y_conf -6 ,672 ,150 ),3 ,border_radius =24 )
        pygame .draw .rect (self .screen ,bg_conf ,conf_rect ,border_radius =24 )
        conf_txt =self ._render_cached (self .font_tiny ,"CONFERMA",WHITE )
        rect_c =conf_txt .get_rect (center =(SCREEN_WIDTH //2 ,y_conf +69 ))
        self .screen .blit (conf_txt ,rect_c )

    def draw_config (self ):
        mx ,my =self ._mouse_pos ()
        overlay =self ._overlay
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        title =self ._render_cached (self .font_title ,"OPZIONI - ALLENAMENTO",GOLD )
        rect =title .get_rect (center =(SCREEN_WIDTH //2 ,240 ))
        self .screen .blit (title ,rect )

        ops =["moltiplicazione","addizione","sottrazione","divisione"]
        op_idx =ops .index (self .config_operation )
        addition =self .config_operation =="addizione"
        subtraction =self .config_operation =="sottrazione"
        division =self .config_operation =="divisione"

        def row_y (r ):
            base =[450 ,630 ,870 ,1110 ,1260 ,1410 ,1560 ,1650 ]
            pools_mode =addition or subtraction or division 
            cell_h ,gap =90 ,18 
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
        label_op =self ._render_cached (self .font_tiny ,"Operazione",WHITE )
        rect =label_op .get_rect (midleft =(240 ,y +51 ))
        self .screen .blit (label_op ,rect )
        opzioni_op =["Moltiplicazione","Addizione","Sottrazione","Divisione"]
        for i ,nome in enumerate (opzioni_op ):
            sx =1080 +i *510 
            sel =i ==op_idx 
            btn_rect =pygame .Rect (sx ,y ,474 ,102 )
            hovered =btn_rect .collidepoint (mx ,my )
            bg_col =(100 ,150 ,220 )if sel and hovered else SEL_BLUE if sel else (80 ,80 ,90 )if hovered else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =12 )
            if hovered :
                pygame .draw .rect (self .screen ,GOLD ,btn_rect ,2 ,border_radius =12 )
            txt =self ._render_cached (self .font_tiny ,nome ,WHITE )
            rect_t =txt .get_rect (center =(sx +237 ,y +51 ))
            self .screen .blit (txt ,rect_t )

            # Row 1-2: Pool A / Pool B (unified 5-col grid)
        labels =["Operando A","Operando B"]
        pools =[self .config ["pool_a"],self .config ["pool_b"]]
        cols_u =5 
        pools_mode =addition or subtraction or division 
        for ri in range (2 ):
            row =1 +ri 
            y_base =row_y (row )
            label =self ._render_cached (self .font_tiny ,labels [ri ],WHITE )
            rect =label .get_rect (midleft =(240 ,y_base +51 ))
            self .screen .blit (label ,rect )

            items =10 if pools_mode else 13 
            subrows =(items +cols_u -1 )//cols_u 
            cell_w ,cell_h =300 ,90 
            gap =18 
            grid_x =1080 
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
                    pygame .draw .rect (self .screen ,bg_col ,cell_rect ,border_radius =12 )
                    if hovered_cell :
                        pygame .draw .rect (self .screen ,GOLD ,cell_rect ,2 ,border_radius =12 )
                    t =self ._render_cached (self .font_tiny ,txt ,WHITE )
                    rt =t .get_rect (center =(sx +cell_w //2 ,sy +cell_h //2 ))
                    self .screen .blit (t ,rt )

                    # Row 3: Somma massima / Differenza positiva
        row =3 
        y =row_y (row )
        if addition :
            label_s =self ._render_cached (self .font_tiny ,"Somma massima",WHITE )
            rect =label_s .get_rect (midleft =(240 ,y +51 ))
            self .screen .blit (label_s ,rect )
            sx =1080 
            lw ,vw ,rw =90 ,120 ,90 
            minus_rect =pygame .Rect (sx ,y ,lw ,102 )
            plus_rect =pygame .Rect (sx +lw +vw ,y ,rw ,102 )
            hover_minus =minus_rect .collidepoint (mx ,my )
            hover_plus =plus_rect .collidepoint (mx ,my )
            pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =12 )
            pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(sx +lw ,y ,vw ,102 ))
            pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =12 )
            if hover_minus :
                pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =12 )
            if hover_plus :
                pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =12 )
            minus =self ._render_cached (self .font_tiny ,"-",WHITE )
            plus =self ._render_cached (self .font_tiny ,"+",WHITE )
            self .screen .blit (minus ,minus .get_rect (center =(sx +lw //2 ,y +51 )))
            self .screen .blit (plus ,plus .get_rect (center =(sx +lw +vw +rw //2 ,y +51 )))
            s_surf =self ._render_cached (self .font_tiny ,str (self .config ["somma_massima"]),WHITE )
            self .screen .blit (s_surf ,s_surf .get_rect (center =(sx +lw +vw //2 ,y +51 )))
        elif subtraction :
            label_d =self ._render_cached (self .font_tiny ,"Differenza positiva",WHITE )
            rect =label_d .get_rect (midleft =(240 ,y +51 ))
            self .screen .blit (label_d ,rect )
            toggle_rect =pygame .Rect (1056 ,y ,558 ,108 )
            hover_toggle =toggle_rect .collidepoint (mx ,my )
            bg_d =(100 ,150 ,220 )if self .config ["differenza_positiva"]and hover_toggle else SEL_BLUE if self .config ["differenza_positiva"]else (80 ,80 ,90 )if hover_toggle else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_d ,toggle_rect ,border_radius =18 )
            if hover_toggle :
                pygame .draw .rect (self .screen ,GOLD ,toggle_rect ,2 ,border_radius =18 )
            dp_txt ="ON"if self .config ["differenza_positiva"]else "OFF"
            dp_val =self ._render_cached (self .font_tiny ,dp_txt ,WHITE )
            rect_dv =dp_val .get_rect (center =(1335 ,y +54 ))
            self .screen .blit (dp_val ,rect_dv )
        elif division :
            label_r =self ._render_cached (self .font_tiny ,"Risultato intero",WHITE )
            rect =label_r .get_rect (midleft =(240 ,y +51 ))
            self .screen .blit (label_r ,rect )
            toggle_rect =pygame .Rect (1056 ,y ,558 ,108 )
            hover_toggle =toggle_rect .collidepoint (mx ,my )
            bg_r =(100 ,150 ,220 )if self .config ["risultato_intero"]and hover_toggle else SEL_BLUE if self .config ["risultato_intero"]else (80 ,80 ,90 )if hover_toggle else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_r ,toggle_rect ,border_radius =18 )
            if hover_toggle :
                pygame .draw .rect (self .screen ,GOLD ,toggle_rect ,2 ,border_radius =18 )
            ri_txt ="ON"if self .config ["risultato_intero"]else "OFF"
            ri_val =self ._render_cached (self .font_tiny ,ri_txt ,WHITE )
            rect_rv =ri_val .get_rect (center =(1335 ,y +54 ))
            self .screen .blit (ri_val ,rect_rv )

            # Row 4: Domande
        row =4 
        y =row_y (row )
        label_q =self ._render_cached (self .font_tiny ,"Domande",WHITE )
        rect =label_q .get_rect (midleft =(240 ,y +51 ))
        self .screen .blit (label_q ,rect )
        qx =1080 
        lw ,vw ,rw =90 ,120 ,90 
        minus_rect =pygame .Rect (qx ,y ,lw ,102 )
        plus_rect =pygame .Rect (qx +lw +vw ,y ,rw ,102 )
        hover_minus =minus_rect .collidepoint (mx ,my )
        hover_plus =plus_rect .collidepoint (mx ,my )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =12 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(qx +lw ,y ,vw ,102 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =12 )
        if hover_minus :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =12 )
        if hover_plus :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =12 )
        minus =self ._render_cached (self .font_tiny ,"-",WHITE )
        plus =self ._render_cached (self .font_tiny ,"+",WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(qx +lw //2 ,y +51 )))
        self .screen .blit (plus ,plus .get_rect (center =(qx +lw +vw +rw //2 ,y +51 )))
        q_surf =self ._render_cached (self .font_tiny ,str (self .config ["domande"]),WHITE )
        self .screen .blit (q_surf ,q_surf .get_rect (center =(qx +lw +vw //2 ,y +51 )))

        # Row 5: Commutazione
        row =5 
        y =row_y (row )
        swap_locked =subtraction 
        toggle_rect =pygame .Rect (1056 ,y ,558 ,108 )
        hover_toggle =toggle_rect .collidepoint (mx ,my )and not swap_locked 
        bg_swap =(100 ,150 ,220 )if (self .config ["swap"]and hover_toggle )else SEL_BLUE if self .config ["swap"]else (80 ,80 ,90 )if hover_toggle else (60 ,60 ,70 )if not swap_locked else (60 ,60 ,70 )
        if swap_locked :
            bg_swap =(60 ,60 ,70 )
        pygame .draw .rect (self .screen ,bg_swap ,toggle_rect ,border_radius =18 )
        if hover_toggle :
            pygame .draw .rect (self .screen ,GOLD ,toggle_rect ,2 ,border_radius =18 )
        sw_txt ="ON"if (self .config ["swap"]or swap_locked )else "OFF"
        swap_label =self ._render_cached (self .font_tiny ,"Commuta A/B",WHITE )
        rect_sl =swap_label .get_rect (midleft =(240 ,y +54 ))
        self .screen .blit (swap_label ,rect_sl )
        swap_val =self ._render_cached (self .font_tiny ,sw_txt ,WHITE )
        rect_sv =swap_val .get_rect (center =(1335 ,y +54 ))
        self .screen .blit (swap_val ,rect_sv )

        # Row 6: Timeout
        row =6 
        y =row_y (row )
        label_t =self ._render_cached (self .font_tiny ,"Timeout (secondi)",WHITE )
        rect =label_t .get_rect (midleft =(240 ,y +51 ))
        self .screen .blit (label_t ,rect )
        tx =1080 
        lw ,vw ,rw =90 ,120 ,90 
        minus_rect =pygame .Rect (tx ,y ,lw ,102 )
        plus_rect =pygame .Rect (tx +lw +vw ,y ,rw ,102 )
        hover_minus =minus_rect .collidepoint (mx ,my )
        hover_plus =plus_rect .collidepoint (mx ,my )
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_minus else (70 ,70 ,80 ),minus_rect ,border_radius =12 )
        pygame .draw .rect (self .screen ,(40 ,40 ,50 ),(tx +lw ,y ,vw ,102 ))
        pygame .draw .rect (self .screen ,(90 ,90 ,100 )if hover_plus else (70 ,70 ,80 ),plus_rect ,border_radius =12 )
        if hover_minus :
            pygame .draw .rect (self .screen ,GOLD ,minus_rect ,2 ,border_radius =12 )
        if hover_plus :
            pygame .draw .rect (self .screen ,GOLD ,plus_rect ,2 ,border_radius =12 )
        minus =self ._render_cached (self .font_tiny ,"-",WHITE )
        plus =self ._render_cached (self .font_tiny ,"+",WHITE )
        self .screen .blit (minus ,minus .get_rect (center =(tx +lw //2 ,y +51 )))
        self .screen .blit (plus ,plus .get_rect (center =(tx +lw +vw +rw //2 ,y +51 )))
        t_surf =self ._render_cached (self .font_tiny ,str (self .config ["timeout"]),WHITE )
        self .screen .blit (t_surf ,t_surf .get_rect (center =(tx +lw +vw //2 ,y +51 )))

        # Row 7: CONFERMA
        row =7 
        y =row_y (row )
        conf_rect =pygame .Rect (SCREEN_WIDTH //2 -330 ,y ,660 ,138 )
        hover_conf =conf_rect .collidepoint (mx ,my )
        bg_conf =(50 ,140 ,50 )if hover_conf else (40 ,120 ,40 )
        if hover_conf :
            pygame .draw .rect (self .screen ,GOLD ,(SCREEN_WIDTH //2 -336 ,y -6 ,672 ,150 ),3 ,border_radius =24 )
        pygame .draw .rect (self .screen ,bg_conf ,conf_rect ,border_radius =24 )
        start_txt =self ._render_cached (self .font_tiny ,"CONFERMA",WHITE )
        rect_s =start_txt .get_rect (center =(SCREEN_WIDTH //2 ,y +69 ))
        self .screen .blit (start_txt ,rect_s )

    def draw_game (self ):
        shake =(0 ,0 )
        boss_shaking =self .boss_active and self .boss_phase =="shake"
        if self .hit_timer >0 or boss_shaking :
            shake =(random .randint (-18 ,18 ),random .randint (-15 ,15 ))
            self .screen .blit (self .game_bg ,shake )
        else :
            self .screen .blit (self .game_bg ,(0 ,0 ))

        if self .scene_npcs :
            now_npc =pygame .time .get_ticks ()
            for npc in self .scene_npcs :
                if self .scene_phase =="exit":
                    frame =npc ["walk"][npc ["walk_idx"]]
                    img =pygame .transform .flip (frame ,True ,False )if npc ["flip_out"]else frame 
                elif self .scene_phase =="enter":
                    walk =npc ["walk"]
                    npc ["walk_idx"]=(now_npc //120 )%len (walk )
                    frame =walk [npc ["walk_idx"]]
                    img =pygame .transform .flip (frame ,True ,False )if npc ["flip_in"]else frame 
                else :
                    frame =self .npc_idle_frame (npc ,now_npc )
                    img =pygame .transform .flip (frame ,True ,False )if npc ["flip_in"]else frame 
                nx =npc ["x"]
                ny =SCREEN_HEIGHT //2 -img .get_height ()//2 +390 +npc ["y_off"]
                self .screen .blit (img ,(nx ,ny ))

        if self .character_entry :
            elapsed =pygame .time .get_ticks ()-self .character_entry_start 
            frame_idx =(elapsed //120 )%4 
            data =self .char_data .get (self .config_gender ,self .char_data ["F"])
            char_img =data ["run"][frame_idx ]
            if self .player_in_dir =="dx":
                char_img =pygame .transform .flip (char_img ,True ,False )
            cw ,ch =char_img .get_size ()
            base_y =SCREEN_HEIGHT //2 -ch //2 
            wy =base_y +390 
            self .screen .blit (char_img ,(self .character_entry_x ,wy ))
            if self .story_fade_alpha >0 :
                fade_surf =self ._overlay
                fade_surf .set_alpha (self .story_fade_alpha )
                fade_surf .fill (self .story_fade_color )
                self .screen .blit (fade_surf ,(0 ,0 ))
            return 
        if self .story_fade_alpha >0 :
            fade_surf =self ._overlay
            fade_surf .set_alpha (self .story_fade_alpha )
            fade_surf .fill (self .story_fade_color )
            self .screen .blit (fade_surf ,(0 ,0 ))
            return 

        wx =self .player_stand_x +shake [0 ]
        data =self .char_data .get (self .config_gender ,self .char_data ["F"])
        is_idle =not self .player_hit and not ((self .question_active and self .input_utente )or self .zap_timer >0 )
        if self .player_shake :
            char_img =data ["shake"]
        elif self .player_hit :
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
        wy =base_y +390 +shake [1 ]
        if is_idle and hasattr (self ,'idle_h')and ch <self .idle_h :
            wy +=(self .idle_h -ch )-(self .idle_h //2 -ch //2 )
        base_h =self .idle_h if hasattr (self ,'idle_h')else ch 
        wy_monster =SCREEN_HEIGHT //2 -base_h //2 +510 +105 +self .monster_y_offset 
        self .screen .blit (char_img ,(wx ,wy ))

        if self .question_active and self .input_utente :
            wand_x =wx +cw -90 if self .player_flip else wx +90 
            glow_x ,glow_y =wand_x ,wy +120 
            base_col =(235 ,220 ,255 )if self .config_gender =="F"else (220 ,255 ,220 )
            t =pygame .time .get_ticks ()
            radius =36 +int (12 *abs ((t %600 )/300 -1 ))
            for r in range (radius ,0 ,-3 ):
                alpha =max (0 ,200 -int (200 *(radius -r )/radius ))
                ratio =(radius -r )/radius 
                col =tuple (max (0 ,int (c *(1 -ratio *0.3 )))for c in base_col )
                surf =pygame .Surface ((r *2 ,r *2 ),pygame .SRCALPHA )
                pygame .draw .circle (surf ,(*col ,alpha ),(r ,r ),r )
                self .screen .blit (surf ,(glow_x -r ,glow_y -r ))

        if self .scene_phase is None and self .boss_active and self .boss_phase in ("entrance","fight","defeated"):
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
                boss_draw_y =wy_monster -(bh -645 )+57 
                self .screen .blit (boss_img ,(boss_draw_x ,boss_draw_y ))
        elif self .scene_phase is None and self .monster_hit :
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
        elif self .scene_phase is None :
            n_frames =len (self .monster_frames )
            self .monster_anim_frame =(pygame .time .get_ticks ()//self .monster_anim_speed )%n_frames 
            self .screen .blit (self .monster_frames [self .monster_anim_frame ],(self .monster_x +shake [0 ],wy_monster ))

        if self .zap_timer >0 :
            start_x ,start_y =(wx +cw -90 )if self .player_flip else (wx +90 ),wy +120 
            if self .zap_reverse :
                end_x ,end_y =wx +cw //2 ,wy +ch //2 
            elif self .boss_active and self .boss_phase in ("entrance","fight","defeated"):
                bw =self .boss_hit_img .get_width ()if self .boss_hit_img else 200 
                bh =self .boss_hit_img .get_height ()if self .boss_hit_img else 200 
                boss_draw_y =wy_monster -(bh -645 )+57 
                end_x ,end_y =self .boss_x +bw //2 ,boss_draw_y +bh //2 
            else :
                end_x ,end_y =self .monster_x +300 ,wy_monster +self .char_h //2 
            mid_x =(start_x +end_x )//2 
            segments =8 
            for offset in range (-4 ,5 ,2 ):
                points =[(start_x ,start_y )]
                for i in range (1 ,segments ):
                    t =i /segments 
                    x =start_x +(end_x -start_x )*t +random .randint (-90 ,90 )
                    y =start_y +(end_y -start_y )*t +random .randint (-120 ,120 )+offset *9 
                    points .append ((x ,y ))
                points .append ((end_x ,end_y ))
                width =9 if abs (offset )<=2 else 3 
                alpha =max (100 ,255 -abs (offset )*40 )
                col =(255 ,255 ,int (255 *self .zap_timer /12 ))if abs (offset )<=2 else (100 ,100 ,255 )
                pygame .draw .lines (self .screen ,col ,False ,points ,width )

        segno =get_operation_symbol (self .operation if hasattr (self ,'operation')else None )
        domanda_text =f"{self .a }  {segno }  {self .b }  =  ?"if self .scene_phase is None else ""
        ombra =self ._render_cached (self .font_large ,domanda_text ,(30 ,30 ,30 ))
        domanda =self ._render_cached (self .font_large ,domanda_text ,WHITE )
        rect =domanda .get_rect (center =(SCREEN_WIDTH //2 ,240 ))
        for dx ,dy in [(-6 ,-6 ),(-6 ,0 ),(-6 ,6 ),(0 ,-6 ),(0 ,6 ),(6 ,-6 ),(6 ,0 ),(6 ,6 )]:
            self .screen .blit (ombra ,(rect .x +dx ,rect .y +dy ))
        self .screen .blit (domanda ,rect )

        if self .question_active :
            text_input =self .input_utente +("|"if pygame .time .get_ticks ()%1000 <500 else " ")
            input_surf =self ._render_cached (self .font_input ,text_input ,WHITE )
            input_rect =input_surf .get_rect (center =(SCREEN_WIDTH //2 ,465 ))
            box_rect =input_rect .inflate (120 ,48 )
            box_rect .width =max (box_rect .width ,360 )
            pygame .draw .rect (self .screen ,(40 ,40 ,60 ),box_rect ,border_radius =24 )
            pygame .draw .rect (self .screen ,(100 ,100 ,180 ),box_rect ,2 ,border_radius =24 )
            ombra =self ._render_cached (self .font_input ,text_input ,(30 ,30 ,30 ))
            self .screen .blit (ombra ,(input_rect .x +6 ,input_rect .y +6 ))
            self .screen .blit (input_surf ,input_rect )

        if not self .level_is_scene :
            if self .mode =="auto":
                stato_txt =f"Livello {self .effective_level ()+1 }/{len (self .levels )}"
                mode_txt ="Storia"
            else :
                stato_txt =f"Domanda {self .questions_asked }/{self .total_questions }"
                mode_txt ="Allenamento"
            mode_surf =self ._render_cached (self .font_small ,mode_txt ,WHITE )
            stato_surf =self ._render_cached (self .font_small ,stato_txt ,WHITE )
            y_top =60 
            self .draw_text_shadow (self .font_small ,mode_txt ,WHITE ,(60 ,y_top ))
            sx_stato =60 +mode_surf .get_width ()+60 
            self .draw_text_shadow (self .font_small ,stato_txt ,WHITE ,(sx_stato ,y_top ))

            for i in range (WIZARD_LIVES ):
                cx =SCREEN_WIDTH -210 -i *150 
                img =self .heart_red if i <self .lives else self .heart_grey 
                self .screen .blit (img ,(cx -51 ,90 ))

        if self .question_active :
            bar_w =1200 
            bar_h =48 
            bar_x =(SCREEN_WIDTH -bar_w )//2 
            bar_y =SCREEN_HEIGHT -135 
            pygame .draw .rect (self .screen ,(60 ,60 ,80 ),(bar_x ,bar_y ,bar_w ,bar_h ),border_radius =24 )
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

            time_text =self ._render_cached (self .font_small ,f"{self .timeout_limit *(1 -timer_progresso ):.0f}s",WHITE )
            rect =time_text .get_rect (midleft =(bar_x +bar_w +45 ,bar_y +bar_h //2 ))
            ombra_t =self ._render_cached (self .font_small ,f"{self .timeout_limit *(1 -timer_progresso ):.0f}s",(30 ,30 ,30 ))
            self .screen .blit (ombra_t ,(rect .x +6 ,rect .y +6 ))
            self .screen .blit (time_text ,rect )

        if self .scene_phase is None and not self .question_active and self .feedback is not None :
            overlay =self ._overlay
            overlay .set_alpha (80 )
            overlay .fill (BLACK )
            self .screen .blit (overlay ,(0 ,0 ))

            if self .feedback :
                fb =self ._render_cached (self .font_large ,"CORRETTO!",GREEN )
                prossimo =self ._render_cached (self .font_small ,"Prossima domanda...",WHITE )
            else :
                fb =self ._render_cached (self .font_large ,f"SBAGLIATO! Era {self .expected_result }",RED )
                prossimo =self ._render_cached (self .font_small ,"Premi INVIO per continuare",WHITE )
            rect =fb .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT //2 -90 ))
            ombra_fb =self ._render_cached (self .font_large ,"CORRETTO!"if self .feedback else f"SBAGLIATO! Era {self .expected_result }",(30 ,30 ,30 ))
            self .screen .blit (ombra_fb ,(rect .x +6 ,rect .y +6 ))
            self .screen .blit (fb ,rect )
            rect =prossimo .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT //2 +90 ))
            ombra_pro =self ._render_cached (self .font_small ,"Prossima domanda..."if self .feedback else "Premi INVIO per continuare",(30 ,30 ,30 ))
            self .screen .blit (ombra_pro ,(rect .x +6 ,rect .y +6 ))
            self .screen .blit (prossimo ,rect )

        if self .monster_hit :
            elapsed =pygame .time .get_ticks ()-self .monster_fade_start 
            white_alpha =max (0 ,150 -int (elapsed /200 *150 ))
            if white_alpha >0 :
                flash =self ._overlay
                flash .set_alpha (white_alpha )
                flash .fill (WHITE )
                self .screen .blit (flash ,(0 ,0 ))

        if self .hit_timer >0 :
            alpha =int (120 *self .hit_timer /12 )
            flash =self ._overlay
            flash .set_alpha (alpha )
            flash .fill (RED )
            self .screen .blit (flash ,(0 ,0 ))

        if self .heart_reward_active :
            elapsed =pygame .time .get_ticks ()-self .heart_reward_start 
            duration =800 
            if elapsed <duration :
                progress =elapsed /duration 
                alpha =int (255 *min (1.0 ,progress *4 )*max (0 ,1.0 -progress ))
                rise =int (360 *progress )
                heart_img =self .heart_red .copy ()
                heart_img .set_alpha (alpha )
                hx =self .monster_x +195 
                hy =wy_monster -rise 
                self .screen .blit (heart_img ,(hx ,hy ))
            else :
                self .heart_reward_active =False 

        if self .scene_phase =="dialogue"and self .scene_npcs :
            self .draw_speech_bubble ()

        if self .debug :
            label =self ._render_cached (self .font_stats ,"DEBUG ON",(0 ,255 ,255 ))
            rect =label .get_rect (bottomright =(SCREEN_WIDTH -45 ,SCREEN_HEIGHT -45 ))
            bg_l =rect .inflate (24 ,12 )
            pygame .draw .rect (self .screen ,(10 ,10 ,20 ),bg_l )
            pygame .draw .rect (self .screen ,(0 ,255 ,255 ),bg_l ,1 )
            self .screen .blit (label ,rect )
            dx ,dy =60 ,240 
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
            bg =pygame .Surface ((1140 ,len (lines )*66 +30 ))
            bg .set_alpha (200 )
            bg .fill ((10 ,10 ,20 ))
            self .screen .blit (bg ,(dx -15 ,dy -15 ))
            for line in lines :
                surf =self ._render_cached (self .font_stats ,line ,(0 ,255 ,255 ))
                rect =surf .get_rect (topleft =(dx ,dy ))
                self .screen .blit (surf ,rect )
                dy +=66 

    def draw_level_complete (self ):
        self .screen .blit (self .game_bg ,(0 ,0 ))
        overlay =self ._overlay
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        self .draw_text_shadow (self .font_title ,f"LIVELLO {self .effective_level ()+1 } COMPLETATO",GOLD ,center =(SCREEN_WIDTH //2 ,240 ))

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

        y =540 
        for text_value ,colore in lines :
            self .draw_text_shadow (self .font_medium ,text_value ,colore ,center =(SCREEN_WIDTH //2 ,y ))
            y +=138 

        self .draw_text_shadow (self .font_small ,"Premi INVIO per continuare",WHITE ,center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -240 ),offset =1 )

    def draw_story (self ):
        entry =self .story_entries [self .story_idx ]if self .story_idx <len (self .story_entries )else {}
        if self .story_is_level and self .story_phase =="exit":
            bg_surf =self .game_bg 
        else :
            bg_name =entry .get ("bg","game")
            bg_surf =self .backgrounds .get (bg_name ,self .bg )
        self .screen .blit (bg_surf ,(0 ,0 ))
        overlay =self ._overlay
        overlay .set_alpha (180 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        text_value =self .story_text_full [:self .story_characters_shown ]

        lines =text_value .split ("\n")
        x_margine =180 
        y =360 
        for line_text in lines :
            words =line_text .split ()
            if not words :
                y +=138 
                continue 
            line =""
            for word in words :
                test =line +" "+word if line else word 
                if self .story_font .size (test )[0 ]>SCREEN_WIDTH -x_margine *2 :
                    self .draw_text_shadow (self .story_font ,line ,WHITE ,midleft =(x_margine ,y ))
                    y +=138 
                    line =word 
                else :
                    line =test 
            if line :
                self .draw_text_shadow (self .story_font ,line ,WHITE ,midleft =(x_margine ,y ))
                y +=138 

        if self .story_phase =="show"and self .story_characters_shown >=len (self .story_text_full ):
            self .draw_text_shadow (self .font_small ,"Premi INVIO per continuare",WHITE ,center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -180 ),offset =1 )

        if self .story_object_img is not None and self .story_object_alpha >0 :
            obj =self .story_object_img .copy ()
            obj .set_alpha (self .story_object_alpha )
            self .screen .blit (obj ,obj .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT //2 )))

        if self .story_fade_alpha >0 :
            fade_surf =self ._overlay
            fade_surf .set_alpha (self .story_fade_alpha )
            fade_surf .fill (self .story_fade_color )
            self .screen .blit (fade_surf ,(0 ,0 ))

    def draw_player_exit (self ):
        if self .player_exit_retry :
            self .screen .blit (self .game_bg ,(0 ,0 ))
            overlay =self ._overlay
            overlay .set_alpha (200 )
            overlay .fill (BG_DARK )
            self .screen .blit (overlay ,(0 ,0 ))
        else :
            self .screen .blit (self .game_bg ,(0 ,0 ))
        for npc in self .scene_npcs :
            frame =self .npc_idle_frame (npc )
            img =pygame .transform .flip (frame ,True ,False )if npc ["flip_in"]else frame 
            nx =npc ["x"]
            ny =SCREEN_HEIGHT //2 -img .get_height ()//2 +390 +npc ["y_off"]
            self .screen .blit (img ,(nx ,ny ))
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
            end_x =SCREEN_WIDTH +600 
        else :
            end_x =-600 
        self .player_exit_x =start_x +(end_x -start_x )*progress 
        base_y =SCREEN_HEIGHT //2 -ch //2 
        wy =base_y +390 
        self .screen .blit (char_img ,(self .player_exit_x ,wy ))

        status =self ._render_cached (self .font_small ,"Salvataggio in corso...",WHITE )
        self .screen .blit (status ,status .get_rect (center =(SCREEN_WIDTH //2 ,SCREEN_HEIGHT -90 )))

    def draw_gameover (self ):
        self .screen .blit (self .game_bg ,(0 ,0 ))
        overlay =self ._overlay
        overlay .set_alpha (200 )
        overlay .fill (BG_DARK )
        self .screen .blit (overlay ,(0 ,0 ))

        if self .mode =="auto":
            self .draw_gameover_story ()
        else :
            self .draw_gameover_fixed ()

    def draw_gameover_story (self ):
        if self .lives <=0 or (self .boss_active and self .boss_phase =="fight"):
            self .draw_text_shadow (self .font_title ,"GAME OVER",RED ,center =(SCREEN_WIDTH //2 ,150 ))
        else :
            self .draw_text_shadow (self .font_title ,"PARTITA TERMINATA",GOLD ,center =(SCREEN_WIDTH //2 ,150 ))

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
        y =330 
        for text_value ,colore in lines :
            self .draw_text_shadow (self .font_medium ,text_value ,colore ,center =(SCREEN_WIDTH //2 ,y ))
            y +=138 

        data =self .char_data .get (self .config_gender ,self .char_data ["F"])
        char_img =data ["hit"]if (self .lives <=0 or (self .boss_active and self .boss_phase =="fight"))else data ["idle"][0 ]
        char_x =SCREEN_WIDTH //2 -char_img .get_width ()//2 
        char_y =y +60 
        self .screen .blit (char_img ,(char_x ,char_y ))

        if self .lives <=0 or (self .boss_active and self .boss_phase =="fight"):
            text_value =f"{self .current_profile } si è impegnat-o-a- parecchio, ma gli Hop diventano man mano più impegnativi. Serve più allenamento!"
            m =self .config_gender =="M"
            text_value =re .sub (r'-([^-]+)-([^-]+)-',lambda g :g .group (1 )if m else g .group (2 ),text_value )
        else :
            text_value =f"Complimenti {self .current_profile }! Hai completato tutti i livelli!"
        lines =[]
        max_w =SCREEN_WIDTH -360 
        for word in text_value .split ():
            if not lines :
                lines .append (word )
            else :
                test =lines [-1 ]+" "+word 
                if self .font_small .size (test )[0 ]>max_w :
                    lines .append (word )
                else :
                    lines [-1 ]=test 

        y_text =char_y +char_img .get_height ()+60 
        for line in lines :
            self .draw_text_shadow (self .font_small ,line ,WHITE ,center =(SCREEN_WIDTH //2 ,y_text ))
            y_text +=105 

        mx ,my =self ._mouse_pos ()
        y_btn =y_text +60 
        self .gameover_buttons ={}
        completato =not (self .lives <=0 or (self .boss_active and self .boss_phase =="fight"))
        btns =[("MENU PRINCIPALE","menu")]if completato else [("RIPROVA","restart"),("MENU PRINCIPALE","menu")]
        btn_w =540 
        total_w =len (btns )*btn_w +(len (btns )-1 )*90 
        start_x =SCREEN_WIDTH //2 -total_w //2 
        for i ,(label ,action )in enumerate (btns ):
            bx =start_x +i *(btn_w +90 )
            btn_rect =pygame .Rect (bx ,y_btn ,btn_w ,108 )
            hovered =btn_rect .collidepoint (mx ,my )
            bg_col =(80 ,90 ,100 )if hovered else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =18 )
            if hovered :
                pygame .draw .rect (self .screen ,GOLD ,btn_rect ,2 ,border_radius =18 )
            self .draw_text_shadow (self .font_small ,label ,WHITE ,center =btn_rect .center )
            self .gameover_buttons [action ]=btn_rect 

    def draw_gameover_fixed (self ):
        if self .lives <=0 :
            self .draw_text_shadow (self .font_title ,"GAME OVER",RED ,center =(SCREEN_WIDTH //2 ,150 ))
        else :
            self .draw_text_shadow (self .font_title ,"PARTITA TERMINATA",GOLD ,center =(SCREEN_WIDTH //2 ,150 ))

        total_correct =sum (v ["corrette"]for v in self .stats .values ())
        total_wrong =sum (v ["sbagliate"]for v in self .stats .values ())
        average_time =sum (self .answer_times )/len (self .answer_times )if self .answer_times else 0 

        lines =[
        (f"Corrette: {total_correct }",GREEN ),
        (f"Sbagliate: {total_wrong }",RED ),
        (f"Vite rimaste: {self .lives }",YELLOW ),
        (f"Tempo medio: {average_time :.1f}s",WHITE ),
        ]
        y =330 
        for text_value ,colore in lines :
            self .draw_text_shadow (self .font_medium ,text_value ,colore ,center =(SCREEN_WIDTH //2 ,y ))
            y +=138 

        sessioni =self .load_sessions ()
        if sessioni :
            y +=42 
            self .draw_text_shadow (self .font_medium ,"Ultime sessioni:",GOLD ,center =(SCREEN_WIDTH //2 ,y ))
            y +=102 
            max_w =SCREEN_WIDTH -200 
            for s in sessioni :
                disp =s 
                if self .font_tiny .size (disp )[0 ]>max_w and len (disp )>24 :
                    disp =disp [:24 ]
                    while self .font_tiny .size (disp )[0 ]>max_w and len (disp )>4 :
                        disp =disp [:-1 ]
                    disp =disp .rstrip ()+"..."
                self .draw_text_shadow (self .font_tiny ,disp ,(180 ,180 ,180 ),center =(SCREEN_WIDTH //2 ,y ))
                y +=72 

        mx ,my =self ._mouse_pos ()
        y =max (y +60 ,SCREEN_HEIGHT -300 )
        self .gameover_buttons ={}
        for i ,(label ,action )in enumerate ([("Ricomincia","restart"),("Menu principale","menu")]):
            bx =SCREEN_WIDTH //2 -300 +i *630 
            btn_rect =pygame .Rect (bx ,y ,540 ,108 )
            hovered =btn_rect .collidepoint (mx ,my )
            bg_col =(80 ,90 ,100 )if hovered else (60 ,60 ,70 )
            pygame .draw .rect (self .screen ,bg_col ,btn_rect ,border_radius =18 )
            if hovered :
                pygame .draw .rect (self .screen ,GOLD ,btn_rect ,2 ,border_radius =18 )
            self .draw_text_shadow (self .font_small ,label ,WHITE ,center =btn_rect .center )
            self .gameover_buttons [action ]=btn_rect 

    def save_session (self ):
        total_correct =sum (v ["corrette"]for v in self .stats .values ())
        total_wrong =sum (v ["sbagliate"]for v in self .stats .values ())
        average_time =sum (self .answer_times )/len (self .answer_times )if self .answer_times else 0 
        now =datetime .now ().strftime ("%Y-%m-%d %H:%M")
        errori_txt =""
        for w in getattr (self ,"wrong_questions",[]):
            if errori_txt :
                errori_txt +=", "
            errori_txt +=format_wrong_entry (*w [:4 ])
        if errori_txt :
            errori_txt =" | Errori: "+errori_txt 
        if self .mode =="auto":
            line_text =f"{now } | Storia | {self .config_story_operation .capitalize ()} | Corrette: {total_correct } | Sbagliate: {total_wrong } | Livello: {self .effective_level ()+1 }/{len (self .levels )} | Tempo medio: {average_time :.1f}s{errori_txt }"
        else :
            op_txt =self .operation .capitalize ()if hasattr (self ,'operation')else "Moltiplicazione"
            pool_a_txt =format_pool_compact (self .pool_a )
            pool_b_txt =format_pool_compact (self .pool_b )
            extra =""
            if self .operation =="sottrazione"and getattr (self ,'differenza_positiva',False ):
                extra =" | Diff. positiva: ON"
            if self .operation =="divisione"and getattr (self ,'risultato_intero',True ):
                extra =" | Ris. intero: ON"
            line_text =f"{now } | Allenamento | {op_txt } | Corrette: {total_correct } | Sbagliate: {total_wrong } | Pool A: [{pool_a_txt }] | Pool B: [{pool_b_txt }] | Domande: {self .questions_asked }/{self .total_questions } | Tempo medio: {average_time :.1f}s{extra }{errori_txt }"
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
        animated_states =("splash","profile_select","game","story","player_exit")
        while self .running :
            events =pygame .event .get ()
            for event in events :
                if event .type ==pygame .QUIT :
                    self .running =False 
                else :
                    self .handle_input (event )
            if events or self .state in animated_states :
                self .update ()
                self .draw ()
                self .clock .tick (FPS )
            else :
                pygame .time .delay (5 )

        pygame .quit ()
        sys .exit ()

if __name__ =="__main__":
    g =Game ()
    g .run ()
