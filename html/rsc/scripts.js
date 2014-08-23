$(document).ready(function() {
    $("#subreddit-input").keypress(function(e)
    {
      if(e.which == 13)
      {
         var subreddit = $("#subreddit-input").val();
         $("#subreddits").append("<div class='subreddit'>" + subreddit + "</div>");
         $("#subreddit-input").val("");
      }
    });
});

$(document).on('click','.subreddit',function()
{
   $(this).fadeOut("fast", function() { this.remove(); });
});

var lastRequst = "";

function init()
{
	sortChange();
	refresh();
}

function enable_load_button(enable)
{
  document.getElementById("load_more_button").disabled = !enable;
}

function buildRequest()
{
	var request = "results?"

	var subreddits = [];
      
        $("#subreddits").children().each(function(index)
        {
	   subreddits.push($(this).text());
        });
	
	for(var i = 0; i < subreddits.length; i++)
	{
	   request += "sub=" + subreddits[i] + "&";
	}

	var sortElement = document.getElementById('sort')
	var sortType = sortElement.options[sortElement.selectedIndex].value;
	request += "sort=" + sortType + "&";

	if(sortType == "top")
	{
		var timeElement = document.getElementById('time')
		request += "time=" + timeElement.options[timeElement.selectedIndex].value;
	}

	if(request.slice(-1) == '&')
	{
		request = request.substring(0, request.length - 1)
	}

	return request;
}

function refresh()
{
	lastRequest = buildRequest();
	enable_load_button(false);
	performRequest(lastRequest, true);
}

function loadMore(button)
{
	var last_id = '';
	var images = document.getElementsByTagName("img");

	if(images.length > 0)
	{
		var lastChild = images[images.length - 1];
		last_id = lastChild.getAttribute('id');
	}
	
	enable_load_button(false);

	request = lastRequest + "&after="+last_id;
	performRequest(request, false);
}

function performRequest(request, clear)
{
	var xmlhttp;
	if (window.XMLHttpRequest)
	{// code for IE7+, Firefox, Chrome, Opera, Safari
		xmlhttp=new XMLHttpRequest();
	}

	xmlhttp.onreadystatechange=function()
	{
		if (xmlhttp.readyState==4 && xmlhttp.status==200)
		{
			if(clear)
			{
				document.getElementById("main_div").innerHTML = ""
			}

			parse_results(xmlhttp.responseText);
		
		  enable_load_button(true);
		}
	}

	xmlhttp.open("GET",request,true);
	xmlhttp.send();
}

function parse_results(response_text)
{
	console.log(response_text);
	var results = JSON.parse(response_text);

	if(results['success'])
	{
		var images = results["data"]["images"];

		for(var i = 0; i < images.length; i++)
		{
			image_html = "<div class='Image'>";
			image_html += "<a href='http://www.reddit.com" + images[i]["reddit_link"] + "' target='_blank' class='Reddit'>";
			image_html += "<img class='Reddit' src='/images/reddit_button.gif' width='12' height='12'/></a>";

			if(images[i]["username"] != "")
			{
				var fav = "False";
				var fav_image = "/images/empty_heart.gif";
				if(images[i]["favorite"])
				{
					fav = "True"
					fav_image = "/images/heart.gif";
				}

				image_html += "<input class='Favorite' favorite='" + fav + "' type='image' id='" + images[i]["name"] + "_button' ";
				image_html += "value='" + images[i]["name"] + "' onClick='favorite(this);' src='" + fav_image + "' ";
				image_html += "width='12' height='12'/>";
			}
			

			image_html += "<a href='" + images[i]["image_link"] + "' target='_blank'>";
			image_html += "<img id='" + images[i]["name"] + "' src='" + images[i]["thumbnail"] + "'/></a>";
			image_html += "</div>";


			document.getElementById("main_div").innerHTML += image_html;
		}
	}
	else
	{
		alert("Error!");
	}
	
}

function sortChange()
{
	var sortComboBox =  document.getElementById('sort');
	var val = sortComboBox.options[sortComboBox.selectedIndex].value;

	if(val != 'top')
	{
		document.getElementById('time').disabled = true;
	}
	else
	{
		document.getElementById('time').disabled = false;
	}
}

function favorite(button)
{
	var request = '/favorite?wall_id=' + button.value;

	if(button.getAttribute("favorite") == 'False')
	{
		request += '&action=add';
	}
	else
	{
		request += '&action=remove';
	}

	var xmlhttp;
	if (window.XMLHttpRequest)
	{// code for IE7+, Firefox, Chrome, Opera, Safari
		xmlhttp=new XMLHttpRequest();
	}

	xmlhttp.onreadystatechange=function()
	{
		if (xmlhttp.readyState==4 && xmlhttp.status==200)
		{
			result = xmlhttp.responseText.split(' ');
			var button_element = document.getElementById(result[1] + '_button');

			if(result[0] == 'add')
			{
				button_element.setAttribute("favorite","True");
				button_element.setAttribute("src","/images/heart.gif");
			}
			else
			{
				button_element.setAttribute("favorite","False");
				button_element.setAttribute("src","/images/empty_heart.gif");
			}
			
		}
	}

	xmlhttp.open("GET",request,true);
	xmlhttp.send();
}
