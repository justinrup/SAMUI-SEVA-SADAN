(function(){
  const root=document.documentElement;

  const get=(key,def)=>{
    try{return localStorage.getItem("sss_"+key)||def}
    catch(e){return def}
  };

  function applySettings(){
    const font=get("fontSize","medium");
    const color=get("textColor","dark");
    const style=get("textStyle","normal");
    const theme=get("theme","default");

    root.dataset.sssFontSize=font;
    root.dataset.sssTextColor=color;
    root.dataset.sssTextStyle=style;
    root.dataset.sssTheme=theme;

    let old=document.getElementById("sss-global-settings-style");
    if(old) old.remove();

    const css=`
      html[data-sss-font-size="small"] body{font-size:90%!important}
      html[data-sss-font-size="medium"] body{font-size:100%!important}
      html[data-sss-font-size="large"] body{font-size:115%!important}
      html[data-sss-font-size="xlarge"] body{font-size:130%!important}

      html[data-sss-text-color="dark"] body{color:#183b4d}
      html[data-sss-text-color="blue"] body{color:#075985}
      html[data-sss-text-color="green"] body{color:#166534}
      html[data-sss-text-color="red"] body{color:#991b1b}

      html[data-sss-text-style="normal"] body{
        font-family:Arial,sans-serif;font-weight:400
      }
      html[data-sss-text-style="bold"] body{
        font-family:Arial,sans-serif;font-weight:700
      }
      html[data-sss-text-style="modern"] body{
        font-family:Arial,sans-serif;letter-spacing:.2px
      }
      html[data-sss-text-style="classic"] body{
        font-family:Georgia,serif
      }

      html[data-sss-theme="default"] body{}
      html[data-sss-theme="blue"] body{
        background:linear-gradient(135deg,#eef9ff,#dff3ff)!important
      }
      html[data-sss-theme="green"] body{
        background:linear-gradient(135deg,#f0fff7,#e0f7ec)!important
      }
      html[data-sss-theme="light"] body{
        background:#ffffff!important
      }
    `;

    const st=document.createElement("style");
    st.id="sss-global-settings-style";
    st.textContent=css;
    document.head.appendChild(st);
  }

  applySettings();

  window.addEventListener("storage",applySettings);
})();
