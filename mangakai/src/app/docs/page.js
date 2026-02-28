"use client";

import { useRouter } from "next/navigation";
import Cookies from "js-cookie";

export default function DocsPage() {
  const router = useRouter();

  const handleLogout = () => {
    Cookies.remove("authToken");
    window.location.href = "/";
  };

  return (
    <section className="p-3 lg:p-8 bg-[url(/859028-anime-snatch-green-background-desktop-wallpaper-1366x768.jpg)] flex justify-center lg:items-center w-full min-h-screen bg-[length:100%_auto] bg-repeat-y bg-center bg-no-repeat-x">
      <div className="bg-white/30 w-full max-w-full md:w-[95%] lg:w-[1280px] xl:w-[1980px] min-h-[85vh] md:min-h-[90%] lg:min-h-[720px] flex-1 rounded-2xl flex flex-col items-center p-3 overflow-auto">
        <div className="grid grid-cols-1 md:grid-cols-1 lg:grid-cols-2 items-center gap-2 md:gap-4 w-full min-h-[20%] shrink-0 p-2 md:p-4">
          {/* LEFT SIDE: Title */}
          <div className="flex justify-center lg:justify-start">
            <p className="bg-[#2f9e44] flex justify-center mt-4 w-[90%] lg:w-[90%] md:w-[50%] px-2 lg:px-6 py-3 rounded-xl text-xl lg:text-3xl text-white">
              Docs
            </p>
          </div>

          {/* RIGHT SIDE: Navigation Buttons */}
          <div className="flex justify-center md:mt-4 lg:justify-end gap-2 lg:gap-4">
            <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={() => router.push("/")}>
              Home
            </button>
            <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={() => router.push("/generateCharacter")}>
              Character
            </button>
            <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={() => router.push("/generatePanel")}>
              Panel
            </button>
            <button className="bg-white text-[#2f9e44] border-[#2f9e44] border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" disabled>
              Doc
            </button>
            <button className="bg-[#2f9e44] text-white border-white border-2 px-2 py:1 md:px-4 md:py-2 rounded-lg text-s md:text-md" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
        <div className="flex flex-1 justify-center items-start md:items-center w-full p-3 sm:p-5 pt-4 md:pt-8 min-h-0">
          <div className="border-5 bg-[#40c057] flex flex-col p-4 sm:p-5 md:p-8 rounded-xl w-full max-w-full md:w-[85%] lg:w-[80%] xl:w-[75%] border-dashed min-h-[300px] md:min-h-[400px] flex-1">
            <div className="text-white/90 text-left space-y-4">
              <h2 className="text-lg font-bold text-white">How to use</h2>
              <div>
                <p className="font-bold text-white">Create your own character</p>
                <p className="mt-1">
                  Go to the Character page and upload your photo, then confirm the character after you see your animefied image. Next, go to the Panel page, write your prompt, and generate. The better the prompt, the better the image.
                </p>
              </div>
              <div>
                <p className="font-bold text-white">Two character panel</p>
                <p className="mt-1">
                  First upload your photo and confirm your character (same as for one character). Then go to Panel and write a two-character prompt; you can mention their dialogue.
                </p>
              </div>
              <div>
                <p className="font-bold text-white">No character Background</p>
                <p className="mt-1">
                  Go to Panel and describe the scene—for example, a cemetery, a demon army charging. This works for generating a background or showing your attack.
                </p>
              </div>
              <h2 className="text-lg font-bold text-white pt-2">How to generate better images</h2>
              <ol className="list-decimal list-inside space-y-1">
                <li>Keep updating your prompts until you get an image that matches your specifications.</li>
                <li>Upload a clear photo of yourself.</li>
                <li>Keep generating again and again with the same prompt; it improves the quality of the output with each run.</li>
              </ol>
              <h2 className="text-lg font-bold text-white pt-2">How to get the panel</h2>
              <p>
                After you generate your image, click the &quot;Download panel&quot; button and it will download the image to your device.
              </p>
              <p className="pt-2">
                If you have any more doubts, contact vedant :)
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
