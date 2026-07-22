using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using UnityEngine.SceneManagement;
using TMPro;

[BepInPlugin("kr.cadriaclord.bigdipper.korean", "Big Dipper Korean", "1.2.2")]
public sealed class BigDipperKoreanSafe : BaseUnityPlugin
{
    private Harmony harmony;
    private static ManualLogSource staticLogger;
    private static readonly HashSet<string> hookedSpeakerNames = new HashSet<string>(StringComparer.Ordinal);
    private static readonly HashSet<string> hookedUiStrings = new HashSet<string>(StringComparer.Ordinal);
    private float nextScan;
    private bool languageReady;
    private bool saveAttempted;
    private bool errorLogged;

    private static readonly Dictionary<string,string> Ui = new Dictionary<string,string>(StringComparer.Ordinal) {
        {"START","시작"},{"NEW GAME","새 게임"},{"CONTINUE","이어하기"},{"RESUME","이어하기"},{"LOAD","불러오기"},{"LOAD GAME","불러오기"},{"SAVE","저장"},{"SAVE OR LOAD","저장 / 불러오기"},
        {"PREFS","설정"},{"AUTO","자동"},{"HISTORY","기록"},{"LOG","기록"},{"SKIP","건너뛰기"},
        {"SETTINGS","설정"},{"OPTIONS","설정"},{"GALLERY","갤러리"},{"CREDITS","제작진"},{"EXIT","종료"},{"QUIT","종료"},{"BACK","뒤로"},{"RETURN","돌아가기"},
        {"YES","예"},{"NO","아니요"},{"MUSIC","음악"},{"SOUND","효과음"},{"SFX","효과음"},{"FULLSCREEN","전체 화면"},{"WINDOWED","창 모드"},
        {"FIN","끝"},{"FIN...","끝…"},
        {"新游戏","새 게임"},{"载入游戏","불러오기"},{"载入","불러오기"},{"读取","불러오기"},{"加载","불러오기"},{"图库","갤러리"},{"画廊","갤러리"},
        {"制作人员","제작진"},{"设置","설정"},{"退出","종료"},{"返回","뒤로"},{"是","예"},{"否","아니요"},{"音乐","음악"},{"音效","효과음"},{"全屏","전체 화면"},
        {"屏幕","화면"},{"显示","화면"},{"文字","텍스트"},{"文本","텍스트"},{"语言","언어"},{"自动","자동"},{"保存","저장"},{"设定","설정"},{"简体中文","한국어"},{"中文","한국어"},
        {"НОВАЯ ИГРА","새 게임"},{"ЗАГРУЗИТЬ","불러오기"},{"Загрузка","불러오기"},{"НАСТРОЙКИ","설정"},{"АВТОРЫ","제작진"},{"ВЫХОД","종료"},
        {"НАЗАД","뒤로"},{"Назад","뒤로"},{"Язык","언어"},{"Экран","화면"},{"Музыка","음악"},{"Звуки","효과음"},{"Текст","텍스트"},
        {"Авто","자동"},{"Сохр.","저장"},{"СОХР","저장"},{"Загр.","불러오기"},{"Настр.","설정"},{"ПОЛНОЭКРАННЫЙ","전체 화면"},
        {"ЗАГРУЗКА","불러오기"},{"СОХРАНЕНИЕ","저장"},{"ГАЛЕРЕЯ","갤러리"},{"ГЛАВНОЕ МЕНЮ","메인 메뉴"},{"СТОП","정지"},
        {"MAIN MENU","메인 메뉴"},{"STOP","정지"},{"主菜单","메인 메뉴"},{"窗口化","창 모드"},{"停止","정지"},
        {"АВТО","자동"},{"ЗАГР.","불러오기"},{"НАСТР.","설정"},{"СОХР.","저장"},{"ЗАГР","불러오기"},{"ОКОННЫЙ","창 모드"},
        {"ДА","예"},{"НЕТ","아니요"},{"Screen","화면"},{"Music","음악"},{"Text","텍스트"},{"Lang","언어"},
        {"РУ","RU"},{"Выйти в главное меню?","메인 메뉴로 돌아갈까요?"},{"ВЕРНУТЬСЯ В ГЛАВНОЕ МЕНЮ БОЛЬШАЯ КНОПКА НА ВЕСЬ ЭКРАН","메인 메뉴로 돌아가기"},
        {"Я","앤드루"},{"Андрей","앤드루"},{"Юля","줄리아"},{"Юля.Девушка","소녀"},{"Девушка","소녀"},{"Дед","니콜라스"},{"Мама","어머니"},
        {"Хорошо…","확인"},{"Хорошо...","확인"},{"Of course...","확인"},{"当然……","확인"},{"New Text","확인"},
        {"Я *убрать","앤드루"},{"Юля *убрать","줄리아"},{"Юля.Девушка *убрать","소녀"},{"Девушка *убрать","소녀"},{"Дед *убрать","니콜라스"},
        {"女孩","소녀"},{"少女","소녀"},{"姑娘","소녀"},{"Girl","소녀"},
        {"茱莉亚","줄리아"},{"母亲","어머니"},{"Mom","어머니"},{"Nicolas","니콜라스"},
        {"Load selected file?","선택한 저장 파일을 불러올까요?"},{"加载所选存档？","선택한 저장 파일을 불러올까요?"},{"Загрузить файл?","선택한 저장 파일을 불러올까요?"},
        {"Override save file?","선택한 저장 파일을 덮어쓸까요?"},{"覆盖所选存档？","선택한 저장 파일을 덮어쓸까요?"},{"Перезаписать файл?","선택한 저장 파일을 덮어쓸까요?"},
        {"Delete save file?","선택한 저장 파일을 삭제할까요?"},{"删除所选存档？","선택한 저장 파일을 삭제할까요?"},{"Удалить файл?","선택한 저장 파일을 삭제할까요?"},
        {"Return to main menu?","메인 메뉴로 돌아갈까요?"},{"回到主菜单？","메인 메뉴로 돌아갈까요?"},{"Вернуться в главное меню?","메인 메뉴로 돌아갈까요?"},
        {"是否载入该存档？","이 저장 데이터를 불러올까요?"},{"是否载入该存档?","이 저장 데이터를 불러올까요?"},
        {"载入这个存档吗？","이 저장 데이터를 불러올까요?"},{"载入这个存档吗?","이 저장 데이터를 불러올까요?"},
        {"读取这个存档吗？","이 저장 데이터를 불러올까요?"},{"读取这个存档吗?","이 저장 데이터를 불러올까요?"},
        {"确定要载入这个存档吗？","이 저장 데이터를 불러올까요?"},{"确定要载入这个存档吗?","이 저장 데이터를 불러올까요?"},
        {"Загрузить это сохранение?","이 저장 데이터를 불러올까요?"},{"Загрузить игру?","게임을 불러올까요?"},
        {"Load this save?","이 저장 데이터를 불러올까요?"},{"Load this game?","게임을 불러올까요?"},
        {"Оказывается, это приятно, когда рядом есть человек, о котором можно заботиться. Долгое время кроме меня в этом доме никого не было, и я был уверен, что мне хорошо одному, но вот появилась Юля, и почему-то я совсем не чувствую себя стеснённым.",
         "누군가를 보살피는 일은 생각보다 즐거웠다. 이 집에는 꽤 오랫동안 나 말고 아무도 없었다. 함께 지낼 사람 따위 필요 없다고 확신했지만, 줄리아가 나타났다고 해서 내 생활이 불편해진 것은 아니었다."}
    };

    private void Awake()
    {
        Logger.LogInfo("Safe Korean patch 1.2.2 loaded");
        staticLogger = Logger;
        harmony = new Harmony("kr.cadriaclord.bigdipper.korean.speaker-hook");
        // Patch only small, stable setters.  Harmony-rewriting the game's large
        // obfuscated DialogueManager.output / ModalPanel.NewChoice bodies can
        // throw while JIT-compiling their ECall wrappers and abort Awake.
        // set_outputChar is the actual game setter used by output(), so this is
        // still the direct speaker-name hook and preserves the internal key.
        InstallHook(typeof(DialogueManagerSpeakerPatch), "DialogueManager.set_outputChar");
        InstallGameTextWriterHooks();
        InstallHook(typeof(TmpTextSetterPatch), "TMP_Text.set_text");
        InstallHook(typeof(TmpTextOnEnablePatch), "TextMeshProUGUI.OnEnable");
        Logger.LogInfo("Required direct hooks installed; initialization continues independently of optional hook failures");
        SceneManager.sceneLoaded += OnSceneLoaded;
        TrySetLanguage();
    }

    private void InstallHook(Type patchType, string label)
    {
        try {
            harmony.CreateClassProcessor(patchType).Patch();
            Logger.LogInfo("Hook installed: " + label);
        } catch (Exception e) {
            Logger.LogError("Hook failed: " + label + " | " + e.GetType().FullName + ": " + e.Message);
        }
    }

    private void InstallGameTextWriterHooks()
    {
        Type[] owners = {
            typeof(ModalPanel), typeof(MainMenu), typeof(OptionsManager),
            typeof(DialogueManager), typeof(SaveLoadManager),
            typeof(CreditsCanvas), typeof(GalleryCanvas)
        };
        MethodInfo prefixMethod = typeof(BigDipperKoreanSafe).GetMethod(
            "GameTextWriterPrefix", BindingFlags.Static | BindingFlags.NonPublic);
        HarmonyMethod prefix = new HarmonyMethod(prefixMethod);
        int installed = 0;
        for (int i = 0; i < owners.Length; i++)
        {
            MethodInfo[] methods = owners[i].GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic |
                BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly);
            for (int j = 0; j < methods.Length; j++)
            {
                MethodInfo method = methods[j];
                ParameterInfo[] parameters = method.GetParameters();
                if (method.ReturnType != typeof(void) || parameters.Length != 2 ||
                    !typeof(TMP_Text).IsAssignableFrom(parameters[0].ParameterType) ||
                    parameters[1].ParameterType != typeof(string)) continue;
                try {
                    harmony.Patch(method, prefix, null, null, null, null);
                    installed++;
                } catch (Exception e) {
                    Logger.LogError("Game text writer hook failed: " + owners[i].Name + "." + method.Name +
                                    " | " + e.GetType().FullName + ": " + e.Message);
                }
            }
        }
        Logger.LogInfo("Direct game text writer hooks installed: " + installed);
    }

    private static void GameTextWriterPrefix(ref string __1, MethodBase __originalMethod)
    {
        string original = __1;
        string mapped = Map(original);
        if (!String.Equals(original, mapped, StringComparison.Ordinal))
        {
            if (hookedUiStrings.Add(original) && staticLogger != null)
                staticLogger.LogInfo("Game text writer hook: " + __originalMethod.DeclaringType.Name +
                                     "." + __originalMethod.Name + " | " + original + " -> " + mapped);
            __1 = mapped;
        }
    }

    private void Start()
    {
        TranslateVisibleText();
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        TranslateVisibleText();
        Logger.LogInfo("Scene UI translated once: " + scene.name);
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
        if (harmony != null) harmony.UnpatchSelf();
    }

    private void Update()
    {
        if (languageReady) return;
        if (Time.unscaledTime < nextScan) return;
        nextScan = Time.unscaledTime + 0.75f;
        TrySetLanguage();
    }

    private void TrySetLanguage()
    {
        try {
            Settings settings = Settings.instance();
            if (settings == null) return;
            settings.currentLanguage = (Settings.lang)2;
            languageReady = true;
            if (!saveAttempted) { saveAttempted = true; settings.saveSettings(); }
            Logger.LogInfo("Korean script slot selected safely (language 2)");
        } catch (Exception e) {
            if (!errorLogged) { errorLogged = true; Logger.LogWarning("Language selection retry: " + e.ToString()); }
        }
    }
    private void TranslateVisibleText()
    {
        // Include inactive menus/panels. Their OnEnable and set_text hooks keep
        // later changes translated, while this one-shot pass fixes serialized
        // scene values such as the menu description.
        TextMeshProUGUI[] texts = Resources.FindObjectsOfTypeAll<TextMeshProUGUI>();
        for (int i=0; i<texts.Length; i++) {
            TextMeshProUGUI t = texts[i];
            if (t == null) continue;
            string mapped = Map(t.text);
            if (!String.Equals(mapped, t.text, StringComparison.Ordinal)) t.text = mapped;
        }
    }

    private static string Map(string s)
    {
        if (String.IsNullOrEmpty(s)) return s;
        string trimmed=s.Trim(); string v;
        if (Ui.TryGetValue(trimmed,out v)) return v;
        v = MapConfirmation(trimmed);
        if (v != null) return v;
        if (s.StartsWith("Дед:",StringComparison.Ordinal)) s="영감님:"+s.Substring(4);
        if (s.StartsWith("Юля:",StringComparison.Ordinal)) s="줄리아:"+s.Substring(5);
        if (s.StartsWith("Андрей:",StringComparison.Ordinal)) s="앤드루:"+s.Substring(7);
        s=s.Replace("安德鲁","앤드루").Replace("安德烈","앤드루").Replace("朱莉娅","줄리아").Replace("尤莉娅","줄리아").Replace("尼古拉斯","니콜라스").Replace("爷爷","영감님").Replace("妈妈","어머니");
        s=s.Replace("Presented by","제작").Replace("Published by","배급")
           .Replace("Character art","캐릭터 원화").Replace("CG art","CG 원화")
           .Replace("Background art","배경 원화").Replace("UI design","UI 디자인")
           .Replace("Programming","프로그래밍").Replace("Scenario","시나리오")
           .Replace("Editing","편집").Replace("English translation","영어 번역")
           .Replace("Music used:","사용 음악:").Replace("Sound effects used:","사용 효과음:")
           .Replace("Special thanks to:","특별 감사:")
           .Replace("Merry Christmas","메리 크리스마스,")
           .Replace("and   a happy new year!","새해 복 많이 받으세요!")
           .Replace("from freesound.org","출처: freesound.org");
        if (s.Contains("메리 크리스마스,"))
            s=s.Replace("a happy new year!","새해 복 많이 받으세요!").Replace("and","");
        return s;
    }

    private static string MapConfirmation(string value)
    {
        if (String.IsNullOrEmpty(value)) return null;
        bool question = value.IndexOf('?') >= 0 || value.IndexOf('？') >= 0;
        if (!question) return null;
        if ((value.Contains("载入") || value.Contains("加载") || value.Contains("读取")) &&
            (value.Contains("存档") || value.Contains("游戏") || value.Contains("记录")))
            return "이 저장 데이터를 불러올까요?";
        if ((value.IndexOf("Загруз", StringComparison.OrdinalIgnoreCase) >= 0) &&
            (value.IndexOf("сохран", StringComparison.OrdinalIgnoreCase) >= 0 || value.IndexOf("игр", StringComparison.OrdinalIgnoreCase) >= 0))
            return "이 저장 데이터를 불러올까요?";
        if (value.IndexOf("load", StringComparison.OrdinalIgnoreCase) >= 0 &&
            (value.IndexOf("save", StringComparison.OrdinalIgnoreCase) >= 0 || value.IndexOf("game", StringComparison.OrdinalIgnoreCase) >= 0))
            return "이 저장 데이터를 불러올까요?";
        return null;
    }

    private static string MapModalQuestion(string value)
    {
        if (String.IsNullOrEmpty(value)) return value;
        string mapped = Map(value);
        if (!String.Equals(mapped, value, StringComparison.Ordinal)) return mapped;
        bool question = value.IndexOf('?') >= 0 || value.IndexOf('？') >= 0;
        if (!question) return value;

        if (value.Contains("载入") || value.Contains("加载") || value.Contains("读取") ||
            value.IndexOf("Загруз", StringComparison.OrdinalIgnoreCase) >= 0 ||
            value.IndexOf("load", StringComparison.OrdinalIgnoreCase) >= 0)
            return "이 저장 데이터를 불러올까요?";
        if (value.Contains("删除") || value.Contains("清除") ||
            value.IndexOf("Удал", StringComparison.OrdinalIgnoreCase) >= 0 ||
            value.IndexOf("delete", StringComparison.OrdinalIgnoreCase) >= 0)
            return "이 저장 데이터를 삭제할까요?";
        if (value.Contains("保存") || value.Contains("覆盖") ||
            value.IndexOf("Сохран", StringComparison.OrdinalIgnoreCase) >= 0 ||
            value.IndexOf("Перезап", StringComparison.OrdinalIgnoreCase) >= 0 ||
            value.IndexOf("save", StringComparison.OrdinalIgnoreCase) >= 0 ||
            value.IndexOf("overwrite", StringComparison.OrdinalIgnoreCase) >= 0 ||
            value.IndexOf("override", StringComparison.OrdinalIgnoreCase) >= 0)
            return "이 슬롯에 저장할까요?";
        if ((value.Contains("主菜单") || value.Contains("菜单") ||
             value.IndexOf("главн", StringComparison.OrdinalIgnoreCase) >= 0 ||
             value.IndexOf("main menu", StringComparison.OrdinalIgnoreCase) >= 0) &&
            (value.Contains("返回") || value.Contains("退出") ||
             value.IndexOf("Вый", StringComparison.OrdinalIgnoreCase) >= 0 ||
             value.IndexOf("return", StringComparison.OrdinalIgnoreCase) >= 0 ||
             value.IndexOf("exit", StringComparison.OrdinalIgnoreCase) >= 0))
            return "메인 메뉴로 돌아갈까요?";
        return value;
    }

    private static string CleanSpeakerToken(string value)
    {
        if (String.IsNullOrEmpty(value)) return String.Empty;
        string token = value.Trim().TrimEnd(':').Trim();
        int command = token.IndexOf("*убрать", StringComparison.Ordinal);
        if (command >= 0) token = token.Substring(0, command).Trim();
        return token;
    }

    private static string MapSpeakerName(string value)
    {
        if (String.IsNullOrEmpty(value)) return value;
        string token = CleanSpeakerToken(value);
        string mapped;
        switch (token)
        {
            case "Я":
            case "Андрей":
            case "安德鲁":
            case "安德烈":
            case "Andrew": mapped = "앤드루"; break;
            case "Юля":
            case "朱莉娅":
            case "尤莉娅":
            case "茱莉亚":
            case "Julia": mapped = "줄리아"; break;
            case "Юля.Девушка":
            case "Девушка":
            case "女孩":
            case "少女":
            case "姑娘":
            case "Girl": mapped = "소녀"; break;
            case "Дед":
            case "尼古拉斯":
            case "爷爷":
            case "Nicholas": mapped = "니콜라스"; break;
            case "Мама":
            case "妈妈":
            case "母亲":
            case "Mom":
            case "Mother": mapped = "어머니"; break;
            case "Nicolas": mapped = "니콜라스"; break;
            default: return value;
        }
        if (hookedSpeakerNames.Add(value) && staticLogger != null)
            staticLogger.LogInfo("Speaker hook: " + value + " -> " + mapped);
        return mapped;
    }

    private static string ResolveOutputDisplayName(string internalName, string displayName)
    {
        string displayToken = CleanSpeakerToken(displayName);
        if (!String.IsNullOrEmpty(displayToken)) return MapSpeakerName(displayToken);
        string nameToken = CleanSpeakerToken(internalName);
        if (String.IsNullOrEmpty(nameToken)) return displayName;
        return MapSpeakerName(nameToken);
    }

    private static bool IsResolvedKoreanSpeaker(string value)
    {
        return value == "앤드루" || value == "줄리아" || value == "소녀" || value == "니콜라스" || value == "어머니";
    }

    [HarmonyPatch(typeof(DialogueManager), "set_outputChar")]
    private static class DialogueManagerSpeakerPatch
    {
        [HarmonyPrefix]
        private static void Prefix(ref string __0)
        {
            __0 = MapSpeakerName(__0);
        }
    }

    [HarmonyPatch(typeof(TMP_Text), "set_text")]
    private static class TmpTextSetterPatch
    {
        [HarmonyPrefix]
        private static void Prefix(ref string __0)
        {
            string original = __0;
            string mapped = Map(original);
            if (!String.Equals(original, mapped, StringComparison.Ordinal))
            {
                if (hookedUiStrings.Add(original) && staticLogger != null)
                    staticLogger.LogInfo("UI text hook: " + original + " -> " + mapped);
                __0 = mapped;
            }
        }
    }

    [HarmonyPatch(typeof(TextMeshProUGUI), "OnEnable")]
    private static class TmpTextOnEnablePatch
    {
        [HarmonyPostfix]
        private static void Postfix(TextMeshProUGUI __instance)
        {
            if (__instance == null) return;
            string original = __instance.text;
            string mapped = Map(original);
            if (!String.Equals(original, mapped, StringComparison.Ordinal))
                __instance.text = mapped;
        }
    }
}





